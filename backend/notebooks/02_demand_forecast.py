"""
Session M2 — Demand Forecast: LightGBM + Baselines + Grid Stress
Produces: demand_forecast_and_baselines.csv.gz, baseline_results.csv,
          grid_stress_risk_bands.csv, forecast_feature_importance.csv
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error
from pathlib import Path
from dotenv import load_dotenv
import logging, warnings, os, time

warnings.filterwarnings("ignore")
load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

start_time = time.time()

DATA_PATH = Path(os.environ.get("DATA_BASE_PATH", "../data"))
OUTPUT_PATH = DATA_PATH / "model_outputs"
OUTPUT_PATH.mkdir(exist_ok=True)

# ── STEP 1 — Load data ──────────────────────────────────────────────────────

logger.info("STEP 1 — Loading input data...")

gen_path = DATA_PATH / "model_inputs_generated" / "feeder_hourly_energy_balance_generated.csv.gz"
provided_path = DATA_PATH / "model_inputs" / "feeder_hourly_energy_balance.csv.gz"
if gen_path.exists():
    feeder_hourly = pd.read_csv(gen_path)
    logger.info(f"  feeder_hourly: GENERATED ({gen_path.name})")
else:
    feeder_hourly = pd.read_csv(provided_path)
    logger.info(f"  feeder_hourly: PROVIDED fallback ({provided_path.name})")

capacity = pd.read_csv(DATA_PATH / "raw_ami_mdm" / "08_feeder_dt_capacity.csv")

for name, df in [("feeder_hourly", feeder_hourly), ("capacity", capacity)]:
    logger.info(f"  {name}: {df.shape}")

# ── STEP 2 — Prepare forecast dataset ───────────────────────────────────────

logger.info("STEP 2 — Preparing forecast dataset...")

feeder_hourly["timestamp_hour_ist"] = pd.to_datetime(feeder_hourly["timestamp_hour_ist"])
feeder_hourly = feeder_hourly.sort_values(["feeder_id_hash", "timestamp_hour_ist"]).reset_index(drop=True)

n_feeders = feeder_hourly["feeder_id_hash"].nunique()
n_rows = len(feeder_hourly)
logger.info(f"  Unique feeders: {n_feeders}")
logger.info(f"  Total rows: {n_rows}")

# ── STEP 3 — Feature engineering ─────────────────────────────────────────────

logger.info("STEP 3 — Feature engineering...")

df = feeder_hourly.copy()
df["month"] = df["timestamp_hour_ist"].dt.month
df["day_of_month"] = df["timestamp_hour_ist"].dt.day
df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
df["loading_pct"] = df["observed_hourly_kwh"] / df["feeder_capacity_kw"] * 100

for col_name, shift_val in [("lag_1h", 1), ("lag_24h", 24), ("lag_168h", 168)]:
    df[col_name] = df.groupby("feeder_id_hash")["observed_hourly_kwh"].shift(shift_val)

df["rolling_mean_24h"] = df.groupby("feeder_id_hash")["observed_hourly_kwh"].transform(
    lambda x: x.shift(1).rolling(24, min_periods=1).mean()
)
df["rolling_std_24h"] = df.groupby("feeder_id_hash")["observed_hourly_kwh"].transform(
    lambda x: x.shift(1).rolling(24, min_periods=1).std()
)
df["rolling_mean_168h"] = df.groupby("feeder_id_hash")["observed_hourly_kwh"].transform(
    lambda x: x.shift(1).rolling(168, min_periods=1).mean()
)

lag_cols = ["lag_1h", "lag_24h", "lag_168h", "rolling_mean_24h", "rolling_std_24h", "rolling_mean_168h"]
for col in lag_cols:
    df[col] = df[col].fillna(df[col].mean())

logger.info(f"  Features added. Shape: {df.shape}")

# ── STEP 4 — Train/test split ───────────────────────────────────────────────

logger.info("STEP 4 — Train/test split...")

max_ts = df["timestamp_hour_ist"].max()
test_start = max_ts - pd.Timedelta(days=14) + pd.Timedelta(hours=1)

train_df = df[df["timestamp_hour_ist"] < test_start].copy()
test_df = df[df["timestamp_hour_ist"] >= test_start].copy()

logger.info(f"  Train: {len(train_df)} rows ({train_df['timestamp_hour_ist'].min()} to {train_df['timestamp_hour_ist'].max()})")
logger.info(f"  Test: {len(test_df)} rows ({test_df['timestamp_hour_ist'].min()} to {test_df['timestamp_hour_ist'].max()})")

# ── STEP 5 — Baselines ──────────────────────────────────────────────────────

logger.info("STEP 5 — Computing baselines...")

test_df = test_df.copy()

prev_day_map = df.set_index(["feeder_id_hash", "timestamp_hour_ist"])["observed_hourly_kwh"]
test_df["baseline_prev_day"] = test_df.apply(
    lambda r: prev_day_map.get((r["feeder_id_hash"], r["timestamp_hour_ist"] - pd.Timedelta(hours=24)), np.nan),
    axis=1,
)

test_df["baseline_prev_week"] = test_df.apply(
    lambda r: prev_day_map.get((r["feeder_id_hash"], r["timestamp_hour_ist"] - pd.Timedelta(hours=168)), np.nan),
    axis=1,
)

hist_avg = train_df.groupby(["feeder_id_hash", "hour", "day_of_week"])["observed_hourly_kwh"].mean()
test_df["baseline_hist_avg"] = test_df.apply(
    lambda r: hist_avg.get((r["feeder_id_hash"], r["hour"], r["day_of_week"]), np.nan),
    axis=1,
)

for bcol in ["baseline_prev_day", "baseline_prev_week", "baseline_hist_avg"]:
    test_df[bcol] = test_df[bcol].fillna(test_df["observed_hourly_kwh"].mean())

# ── STEP 6 — Train LightGBM ─────────────────────────────────────────────────

logger.info("STEP 6 — Training LightGBM...")

feature_cols = [
    "hour", "day_of_week", "is_weekend", "is_holiday",
    "month", "day_of_month",
    "hour_sin", "hour_cos", "dow_sin", "dow_cos",
    "temperature_2m_c", "relative_humidity_2m_pct",
    "rain_mm", "apparent_temperature_c",
    "lag_1h", "lag_24h", "lag_168h",
    "rolling_mean_24h", "rolling_std_24h", "rolling_mean_168h",
    "feeder_capacity_kw",
]
target_col = "observed_hourly_kwh"

val_size = int(len(train_df) * 0.1)
t_df = train_df.iloc[:-val_size]
v_df = train_df.iloc[-val_size:]

X_train = t_df[feature_cols]
y_train = t_df[target_col]
X_val = v_df[feature_cols]
y_val = v_df[target_col]
X_test = test_df[feature_cols]
y_test = test_df[target_col]

model = lgb.LGBMRegressor(
    objective="regression",
    metric="mae",
    boosting_type="gbdt",
    num_leaves=63,
    learning_rate=0.05,
    feature_fraction=0.8,
    bagging_fraction=0.8,
    bagging_freq=5,
    verbose=-1,
    n_estimators=500,
)

model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    callbacks=[lgb.log_evaluation(100), lgb.early_stopping(50)],
)

logger.info(f"  Best iteration: {model.best_iteration_}")
val_pred = model.predict(X_val)
val_mae = mean_absolute_error(y_val, val_pred)
logger.info(f"  Validation MAE: {val_mae:.2f} kWh")

# ── STEP 7 — Predict and evaluate ───────────────────────────────────────────

logger.info("STEP 7 — Predicting and evaluating...")

test_predictions = model.predict(X_test)
test_predictions = np.maximum(test_predictions, 0)

methods = {
    "Aletheon_LightGBM": test_predictions,
    "Previous_Day_Same_Hour": test_df["baseline_prev_day"].values,
    "Previous_Week_Same_Hour": test_df["baseline_prev_week"].values,
    "Historical_Average": test_df["baseline_hist_avg"].values,
}

results = []
for name, preds in methods.items():
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    wmape = np.sum(np.abs(y_test.values - preds)) / np.sum(y_test.values) * 100
    results.append({"model_or_baseline": name, "MAE_kWh": round(mae, 2),
                     "RMSE_kWh": round(rmse, 2), "WMAPE_pct": round(wmape, 2)})

results_df = pd.DataFrame(results)
our_wmape = results_df.loc[results_df["model_or_baseline"] == "Aletheon_LightGBM", "WMAPE_pct"].values[0]
prev_day_wmape = results_df.loc[results_df["model_or_baseline"] == "Previous_Day_Same_Hour", "WMAPE_pct"].values[0]
results_df["improvement_vs_prev_day_pct"] = round(
    (prev_day_wmape - results_df["WMAPE_pct"]) / prev_day_wmape * 100, 2
)

logger.info("  Model comparison:")
for _, row in results_df.iterrows():
    logger.info(f"    {row['model_or_baseline']}: MAE={row['MAE_kWh']}, "
                f"RMSE={row['RMSE_kWh']}, WMAPE={row['WMAPE_pct']}%")

# ── STEP 8 — Prediction intervals ───────────────────────────────────────────

logger.info("STEP 8 — Computing prediction intervals...")

residuals = y_val.values - val_pred
p10_offset = np.percentile(residuals, 10)
p90_offset = np.percentile(residuals, 90)

test_df = test_df.copy()
test_df["forecast_kwh"] = test_predictions
test_df["forecast_p10"] = np.maximum(test_predictions + p10_offset, 0)
test_df["forecast_p90"] = np.maximum(test_predictions + p90_offset, 0)

# ── STEP 9 — Save demand_forecast_and_baselines.csv.gz ──────────────────────

logger.info("STEP 9 — Generating full forecast...")

train_predictions = model.predict(train_df[feature_cols])
train_predictions = np.maximum(train_predictions, 0)

train_out = train_df.copy()
train_out["forecast_kwh"] = train_predictions
train_out["forecast_p10"] = np.maximum(train_predictions + p10_offset, 0)
train_out["forecast_p90"] = np.maximum(train_predictions + p90_offset, 0)
train_out["baseline_prev_day"] = np.nan
train_out["baseline_prev_week"] = np.nan
train_out["baseline_hist_avg"] = np.nan
train_out["is_test_set"] = 0

test_out = test_df.copy()
test_out["is_test_set"] = 1

full_out = pd.concat([train_out, test_out], ignore_index=True)
full_out = full_out.sort_values(["feeder_id_hash", "timestamp_hour_ist"]).reset_index(drop=True)
full_out.rename(columns={"observed_hourly_kwh": "actual_kwh"}, inplace=True)

out_cols = [
    "timestamp_hour_ist", "zone", "locality", "feeder_id_hash",
    "actual_kwh", "forecast_kwh", "forecast_p10", "forecast_p90",
    "baseline_prev_day", "baseline_prev_week", "baseline_hist_avg",
    "temperature_2m_c", "rain_mm", "is_holiday",
    "loading_pct", "feeder_capacity_kw", "hour", "day_of_week",
    "is_test_set",
]

forecast_out = full_out[out_cols]
forecast_out.to_csv(OUTPUT_PATH / "demand_forecast_and_baselines.csv.gz",
                    index=False, compression="gzip")
logger.info(f"  Saved: {len(forecast_out)} rows, {forecast_out['feeder_id_hash'].nunique()} feeders")

# ── STEP 10 — Save baseline_results.csv ─────────────────────────────────────

logger.info("STEP 10 — Saving baseline_results.csv...")

results_df.to_csv(OUTPUT_PATH / "baseline_results.csv", index=False)
logger.info(f"  Saved: {len(results_df)} rows")

# ── STEP 11 — Save forecast_feature_importance.csv ──────────────────────────

logger.info("STEP 11 — Saving forecast_feature_importance.csv...")

importance_gain = model.booster_.feature_importance(importance_type="gain")
importance_split = model.booster_.feature_importance(importance_type="split")

fi_df = pd.DataFrame({
    "feature_name": feature_cols,
    "importance_gain": importance_gain,
    "importance_split": importance_split,
})
fi_df = fi_df.sort_values("importance_gain", ascending=False).reset_index(drop=True)
fi_df["rank"] = range(1, len(fi_df) + 1)

fi_df.to_csv(OUTPUT_PATH / "forecast_feature_importance.csv", index=False)
logger.info(f"  Top 5 features: {fi_df['feature_name'].head(5).tolist()}")

# ── STEP 12 — Grid stress risk bands ────────────────────────────────────────

logger.info("STEP 12 — Computing grid stress risk bands (forecast-based)...")

feeder_cap = capacity[capacity["asset_type"] == "FEEDER"][
    ["feeder_id_hash", "capacity_kw", "amber_threshold_pct", "red_threshold_pct"]
].rename(columns={"capacity_kw": "physical_feeder_capacity_kw"})

test_forecast = test_df[["timestamp_hour_ist", "feeder_id_hash", "forecast_kwh", "feeder_capacity_kw"]].copy()
test_forecast = test_forecast.merge(feeder_cap, on="feeder_id_hash", how="left")
test_forecast["amber_threshold_pct"] = test_forecast["amber_threshold_pct"].fillna(78)
test_forecast["red_threshold_pct"] = test_forecast["red_threshold_pct"].fillna(92)

test_forecast["forecast_loading_pct"] = (
    test_forecast["forecast_kwh"] / test_forecast["feeder_capacity_kw"] * 100
)

grid_rows = []
for fdr, grp in test_forecast.groupby("feeder_id_hash"):
    peak_idx = grp["forecast_kwh"].idxmax()
    peak_row = grp.loc[peak_idx]
    peak_kwh = peak_row["forecast_kwh"]
    cap_kw = peak_row["feeder_capacity_kw"]
    peak_pct = peak_kwh / cap_kw * 100
    peak_ts = peak_row["timestamp_hour_ist"]
    amber_thresh = peak_row["amber_threshold_pct"]
    red_thresh = peak_row["red_threshold_pct"]
    phys_cap = peak_row.get("physical_feeder_capacity_kw", cap_kw)

    red_hours = (grp["forecast_loading_pct"] >= red_thresh).sum()
    amber_hours = ((grp["forecast_loading_pct"] >= amber_thresh) & (grp["forecast_loading_pct"] < red_thresh)).sum()

    if red_hours > 0:
        band = "RED"
        action = "Immediate load shedding review required"
        team = "O&M + Control Room"
    elif amber_hours > 0:
        band = "AMBER"
        action = "Monitor feeder, prepare contingency"
        team = "O&M"
    else:
        band = "GREEN"
        action = "Normal operations"
        team = "O&M"

    loc_row = feeder_hourly[feeder_hourly["feeder_id_hash"] == fdr].iloc[0]
    grid_rows.append({
        "feeder_id_hash": fdr,
        "locality": loc_row["locality"],
        "zone": loc_row["zone"],
        "peak_forecast_kwh": round(peak_kwh, 2),
        "peak_load_pct": round(peak_pct, 2),
        "peak_time_ist": peak_ts,
        "red_hours": int(red_hours),
        "amber_hours": int(amber_hours),
        "effective_capacity_kw_for_risk": round(cap_kw, 2),
        "physical_feeder_capacity_kw": round(phys_cap if not pd.isna(phys_cap) else cap_kw, 2),
        "grid_risk_band": band,
        "recommended_team": team,
        "recommended_action": action,
    })

grid_df = pd.DataFrame(grid_rows)
grid_df.to_csv(OUTPUT_PATH / "grid_stress_risk_bands.csv", index=False)

red_count = (grid_df["grid_risk_band"] == "RED").sum()
amber_count = (grid_df["grid_risk_band"] == "AMBER").sum()
green_count = (grid_df["grid_risk_band"] == "GREEN").sum()
logger.info(f"  Grid stress: RED={red_count}, AMBER={amber_count}, GREEN={green_count}")

elapsed = time.time() - start_time
logger.info("")
logger.info("=" * 60)
logger.info("M2 DEMAND FORECAST COMPLETE")
logger.info("=" * 60)
logger.info(f"  demand_forecast_and_baselines.csv.gz: {len(forecast_out)} rows")
logger.info(f"  baseline_results.csv: {len(results_df)} rows")
logger.info(f"  forecast_feature_importance.csv: {len(fi_df)} rows")
logger.info(f"  grid_stress_risk_bands.csv: {len(grid_df)} feeders")
logger.info(f"  Total time: {elapsed:.1f}s")
logger.info("=" * 60)

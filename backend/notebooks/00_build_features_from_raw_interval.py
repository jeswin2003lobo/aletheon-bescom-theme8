"""
Aletheon M0: Raw Feature Engineering from 15-Minute Interval Data
=================================================================
Reads the FULL 4,147,200 readings (360 meters x 11,520 intervals)
from NPZ matrix parts and engineers meter summary features and
feeder hourly energy balance.

Input:  raw_ami_mdm/matrix_parts/*.npz  (full 4.1M readings)
Output: model_inputs_generated/meter_summary_features_generated.csv
        model_inputs_generated/feeder_hourly_energy_balance_generated.csv.gz
"""

import pandas as pd
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from scipy.stats import rankdata
import logging
import time
import warnings
import os

warnings.filterwarnings("ignore")
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DATA_PATH = Path(os.environ.get("DATA_BASE_PATH", "../data"))
OUTPUT_PATH = DATA_PATH / "model_inputs_generated"
OUTPUT_PATH.mkdir(exist_ok=True)

SIGNAL_KEYS = [
    "import_kwh",
    "export_kwh",
    "avg_voltage_v",
    "avg_current_a",
    "avg_power_factor",
    "cum_import_kwh",
    "cum_export_kwh",
    "quality_code_id",
    "vee_status_id",
    "outage_flag",
    "communication_status_id",
]

pipeline_start = time.time()


# ── STEP 1: Load full NPZ matrix ────────────────────────────────

logger.info("STEP 1 — Loading full NPZ matrix parts...")

matrix_dir = DATA_PATH / "raw_ami_mdm" / "matrix_parts"
part_files = [
    "aletheon_v3_full_interval_matrix_part01_days001_030.npz",
    "aletheon_v3_full_interval_matrix_part02_days031_060.npz",
    "aletheon_v3_full_interval_matrix_part03_days061_090.npz",
    "aletheon_v3_full_interval_matrix_part04_days091_120.npz",
]

parts = []
for pf in part_files:
    path = matrix_dir / pf
    if not path.exists():
        raise FileNotFoundError(f"Missing NPZ part: {path}")
    parts.append(np.load(path))
    logger.info(f"  Loaded {pf}")

full = {}
for key in SIGNAL_KEYS:
    full[key] = np.concatenate([p[key] for p in parts], axis=1)
    assert full[key].shape == (360, 11520), f"{key} shape mismatch: {full[key].shape}"

logger.info(f"Full matrix: 360 x 11520 = {360 * 11520:,} readings")
logger.info(f"Arrays loaded: {list(full.keys())}")

matrix_index = pd.read_csv(DATA_PATH / "raw_ami_mdm" / "01_meter_interval_matrix_index.csv")
timestamps = pd.read_csv(DATA_PATH / "raw_ami_mdm" / "01_interval_timestamps_15min.csv")
daily_register = pd.read_csv(
    DATA_PATH / "raw_ami_mdm" / "02_meter_register_daily.csv.gz", compression="gzip"
)
comm_health = pd.read_csv(
    DATA_PATH / "raw_ami_mdm" / "04_communication_health.csv.gz", compression="gzip"
)
consumer = pd.read_csv(DATA_PATH / "raw_ami_mdm" / "06_consumer_service_point.csv")
network_gis = pd.read_csv(DATA_PATH / "raw_ami_mdm" / "07_network_gis_mapping.csv")
feeder_system = pd.read_csv(
    DATA_PATH / "raw_ami_mdm" / "10_system_meter_interval_15min_feeder_sample.csv.gz",
    compression="gzip",
)
capacity = pd.read_csv(DATA_PATH / "raw_ami_mdm" / "08_feeder_dt_capacity.csv")
weather = pd.read_csv(DATA_PATH / "external_enrichment" / "weather_bengaluru_hourly.csv")
holidays = pd.read_csv(DATA_PATH / "external_enrichment" / "holiday_festival_calendar.csv")

logger.info(f"  matrix_index: {matrix_index.shape}")
logger.info(f"  timestamps: {timestamps.shape}")
logger.info(f"  daily_register: {daily_register.shape}")
logger.info(f"  comm_health: {comm_health.shape}")
logger.info(f"  consumer: {consumer.shape}")
logger.info(f"  network_gis: {network_gis.shape}")
logger.info(f"  feeder_system: {feeder_system.shape}")
logger.info(f"  capacity: {capacity.shape}")
logger.info(f"  weather: {weather.shape}")
logger.info(f"  holidays: {holidays.shape}")

# Parse timestamp info for hour/weekday calculations
ts_df = timestamps.copy()
ts_df["dt"] = pd.to_datetime(ts_df["read_start_ts_ist"])
ts_df["hour"] = ts_df["dt"].dt.hour
ts_df["weekday"] = ts_df["dt"].dt.weekday  # 0=Mon, 6=Sun
ts_df["date"] = ts_df["dt"].dt.date

hours_array = ts_df["hour"].values  # shape (11520,)
weekday_array = ts_df["weekday"].values


# ── STEP 2: Build meter summary features from full matrix ────────

logger.info("STEP 2 — Building meter summary features from 4.1M readings...")

import_kwh = full["import_kwh"]  # (360, 11520)
quality_code = full["quality_code_id"]  # 0=RAW, 1=MISSING, 2=RAW_OUTAGE_ZERO
outage_flag = full["outage_flag"]
pf_matrix = full["avg_power_factor"]

n_meters = 360
n_intervals = 11520

# 30-day windows (each 30 days = 2880 intervals at 15-min)
first_30 = import_kwh[:, 0:2880]
prev_30 = import_kwh[:, 5760:8640]
last_30 = import_kwh[:, 8640:11520]

first30_kwh = np.nansum(first_30, axis=1)
prev30_kwh = np.nansum(prev_30, axis=1)
last30_kwh = np.nansum(last_30, axis=1)

with np.errstate(divide="ignore", invalid="ignore"):
    drop_first_to_last_pct = np.where(
        first30_kwh > 0,
        (first30_kwh - last30_kwh) / first30_kwh * 100,
        0.0,
    )
    drop_prev_to_last_pct = np.where(
        prev30_kwh > 0,
        (prev30_kwh - last30_kwh) / prev30_kwh * 100,
        0.0,
    )

# Missing and outage percentages
missing_count = np.sum(quality_code == 1, axis=1)
missing_pct = missing_count / n_intervals * 100

outage_count = np.sum(outage_flag == 1, axis=1)
outage_pct = outage_count / n_intervals * 100

# After-hours ratio
business_mask = (hours_array >= 8) & (hours_array < 18) & (weekday_array < 5)
after_mask = ~business_mask

business_kwh = np.nansum(import_kwh[:, business_mask], axis=1)
after_kwh = np.nansum(import_kwh[:, after_mask], axis=1)
with np.errstate(divide="ignore", invalid="ignore"):
    after_hours_ratio = np.where(business_kwh > 0, after_kwh / business_kwh, 0.0)

# Power factor stats
avg_power_factor = np.nanmean(pf_matrix, axis=1)
min_power_factor = np.nanmin(pf_matrix, axis=1)

# Plateau detection: longest consecutive run of identical readings
logger.info("  Computing plateau detection across 4.1M readings...")
plateau_max = np.zeros(n_meters, dtype=int)
for i in range(n_meters):
    row = import_kwh[i, :]
    diffs = np.abs(np.diff(row))
    is_plateau = diffs < 0.001
    if not np.any(is_plateau):
        plateau_max[i] = 1
        continue
    changes = np.diff(is_plateau.astype(int))
    starts = np.where(changes == 1)[0]
    ends = np.where(changes == -1)[0]
    if is_plateau[0]:
        starts = np.concatenate([[0], starts])
    if is_plateau[-1]:
        ends = np.concatenate([ends, [len(is_plateau)]])
    if len(starts) == 0 or len(ends) == 0:
        plateau_max[i] = 1
        continue
    min_len = min(len(starts), len(ends))
    runs = ends[:min_len] - starts[:min_len] + 1
    plateau_max[i] = int(np.max(runs)) if len(runs) > 0 else 1

# Build base dataframe
meter_features = matrix_index[
    [
        "matrix_row",
        "meter_id_hash",
        "service_point_id_hash",
        "feeder_id_hash",
        "dt_id_hash",
        "locality",
        "consumer_category",
        "premise_subtype",
    ]
].copy()

meter_features["first30_kwh"] = np.round(first30_kwh, 2)
meter_features["prev30_kwh"] = np.round(prev30_kwh, 2)
meter_features["last30_kwh"] = np.round(last30_kwh, 2)
meter_features["drop_first_to_last_pct"] = np.round(drop_first_to_last_pct, 2)
meter_features["drop_prev_to_last_pct"] = np.round(drop_prev_to_last_pct, 2)
meter_features["missing_pct"] = np.round(missing_pct, 2)
meter_features["outage_pct"] = np.round(outage_pct, 2)
meter_features["after_hours_ratio"] = np.round(after_hours_ratio, 2)
meter_features["avg_power_factor"] = np.round(avg_power_factor, 2)
meter_features["min_power_factor"] = np.round(min_power_factor, 2)
meter_features["plateau_max_run_intervals"] = plateau_max

logger.info(f"  Base features computed for {len(meter_features)} meters")


# ── STEP 3: Peer comparison with fallback hierarchy ──────────────

logger.info("STEP 3 — Building peer comparison features...")

# Join zone from network_gis
gis_zone = network_gis[["meter_id_hash", "zone"]].drop_duplicates("meter_id_hash")
meter_features = meter_features.merge(gis_zone, on="meter_id_hash", how="left")

# Join consumer data
consumer_cols = consumer[
    [
        "service_point_id_hash",
        "tariff_category",
        "sanctioned_load_kw",
        "gruha_jyothi_eligible",
        "solar_capacity_kw",
        "ev_flag",
        "occupancy_pattern",
        "monthly_baseline_units",
        "net_metering_flag",
    ]
].copy()
meter_features = meter_features.merge(consumer_cols, on="service_point_id_hash", how="left")


def compute_peer_ranks(df):
    """Assign peer group using 4-level fallback, then compute percentile ranks."""
    peer_group = []
    peer_group_level = []
    peer_group_size = []
    peer_rank_first30 = []
    peer_rank_last30 = []

    for idx, row in df.iterrows():
        loc = str(row.get("locality", ""))
        zone = str(row.get("zone", ""))
        cat = str(row.get("consumer_category", ""))
        sub = str(row.get("premise_subtype", ""))

        levels = [
            (1, f"{loc}|{cat}|{sub}"),
            (2, f"{loc}|{cat}"),
            (3, f"{zone}|{cat}"),
            (4, cat),
        ]

        chosen_level = 4
        chosen_group = cat
        chosen_mask = df["consumer_category"] == cat

        for lvl, grp_key in levels:
            if lvl == 1:
                mask = (
                    (df["locality"] == loc)
                    & (df["consumer_category"] == cat)
                    & (df["premise_subtype"] == sub)
                )
            elif lvl == 2:
                mask = (df["locality"] == loc) & (df["consumer_category"] == cat)
            elif lvl == 3:
                mask = (df["zone"] == zone) & (df["consumer_category"] == cat)
            else:
                mask = df["consumer_category"] == cat

            if mask.sum() >= 3:
                chosen_level = lvl
                chosen_group = grp_key
                chosen_mask = mask
                break

        peer_vals_first = df.loc[chosen_mask, "first30_kwh"].values
        peer_vals_last = df.loc[chosen_mask, "last30_kwh"].values
        my_first = row["first30_kwh"]
        my_last = row["last30_kwh"]

        if len(peer_vals_first) > 1:
            rank_f = (rankdata(peer_vals_first, method="average") /
                      len(peer_vals_first) * 100)
            my_idx = np.where(chosen_mask.values)[0]
            local_idx = np.where(np.where(chosen_mask.values)[0] == idx)[0]
            if len(local_idx) > 0:
                rf = round(rank_f[local_idx[0]], 1)
            else:
                rf = round(
                    np.sum(peer_vals_first <= my_first) / len(peer_vals_first) * 100, 1
                )

            rank_l = (rankdata(peer_vals_last, method="average") /
                      len(peer_vals_last) * 100)
            if len(local_idx) > 0:
                rl = round(rank_l[local_idx[0]], 1)
            else:
                rl = round(
                    np.sum(peer_vals_last <= my_last) / len(peer_vals_last) * 100, 1
                )
        else:
            rf = 50.0
            rl = 50.0

        peer_group.append(chosen_group)
        peer_group_level.append(chosen_level)
        peer_group_size.append(int(chosen_mask.sum()))
        peer_rank_first30.append(rf)
        peer_rank_last30.append(rl)

    df["peer_group"] = peer_group
    df["peer_group_level"] = peer_group_level
    df["peer_group_size"] = peer_group_size
    df["peer_rank_first30"] = peer_rank_first30
    df["peer_rank_last30"] = peer_rank_last30
    df["peer_rank_drop_points"] = [
        round(f - l, 1) for f, l in zip(peer_rank_first30, peer_rank_last30)
    ]
    return df


meter_features = compute_peer_ranks(meter_features)

level_dist = meter_features["peer_group_level"].value_counts().sort_index()
logger.info("  Peer group level distribution:")
for lvl, cnt in level_dist.items():
    labels = {1: "specific", 2: "locality", 3: "zone", 4: "category"}
    logger.info(f"    Level {lvl} ({labels.get(lvl, '?')}): {cnt} meters")


# ── STEP 4: Save meter_summary_features_generated.csv ────────────

logger.info("STEP 4 — Saving meter summary features...")

output_cols = [
    "meter_id_hash",
    "service_point_id_hash",
    "locality",
    "zone",
    "feeder_id_hash",
    "dt_id_hash",
    "consumer_category",
    "premise_subtype",
    "tariff_category",
    "first30_kwh",
    "prev30_kwh",
    "last30_kwh",
    "drop_first_to_last_pct",
    "drop_prev_to_last_pct",
    "missing_pct",
    "outage_pct",
    "after_hours_ratio",
    "avg_power_factor",
    "min_power_factor",
    "plateau_max_run_intervals",
    "monthly_baseline_units",
    "sanctioned_load_kw",
    "gruha_jyothi_eligible",
    "solar_capacity_kw",
    "ev_flag",
    "occupancy_pattern",
    "peer_group",
    "peer_group_level",
    "peer_group_size",
    "peer_rank_first30",
    "peer_rank_last30",
    "peer_rank_drop_points",
]

meter_out = meter_features[output_cols].copy()
meter_out.to_csv(OUTPUT_PATH / "meter_summary_features_generated.csv", index=False)
logger.info(
    f"  Saved: meter_summary_features_generated.csv "
    f"({len(meter_out)} rows, {len(output_cols)} columns)"
)


# ── STEP 5: Build feeder hourly energy balance from raw ──────────

logger.info("STEP 5 — Building feeder hourly energy balance from system meters...")

feeder_system["read_start_ts_ist"] = pd.to_datetime(feeder_system["read_start_ts_ist"])
feeder_system["hour_ts"] = feeder_system["read_start_ts_ist"].dt.floor("h")

feeder_hourly = (
    feeder_system.groupby(["feeder_id_hash", "hour_ts"])
    .agg(observed_hourly_kwh=("import_kwh", "sum"))
    .reset_index()
)

feeder_hourly["observed_avg_kw"] = feeder_hourly["observed_hourly_kwh"]

# Add feeder metadata (locality, zone, capacity)
feeder_cap = capacity[capacity["asset_type"] == "FEEDER"][
    ["feeder_id_hash", "locality", "zone", "capacity_kw"]
].drop_duplicates("feeder_id_hash")
feeder_cap = feeder_cap.rename(columns={"capacity_kw": "feeder_capacity_kw"})

feeder_hourly = feeder_hourly.merge(feeder_cap, on="feeder_id_hash", how="left")

# Add weather
weather["timestamp_hour_ist"] = pd.to_datetime(weather["timestamp_hour_ist"])
feeder_hourly = feeder_hourly.merge(
    weather,
    left_on="hour_ts",
    right_on="timestamp_hour_ist",
    how="left",
)

# Add time features
feeder_hourly["hour"] = feeder_hourly["hour_ts"].dt.hour
feeder_hourly["day_of_week"] = feeder_hourly["hour_ts"].dt.weekday
feeder_hourly["is_weekend"] = (feeder_hourly["day_of_week"] >= 5).astype(int)

# Add holiday flag
holiday_dates = set(pd.to_datetime(holidays["date"]).dt.date)
feeder_hourly["date"] = feeder_hourly["hour_ts"].dt.date
feeder_hourly["is_holiday"] = feeder_hourly["date"].apply(
    lambda d: 1 if d in holiday_dates else 0
)

# Format output
feeder_hourly["timestamp_hour_ist"] = feeder_hourly["hour_ts"].dt.strftime(
    "%Y-%m-%d %H:%M:%S"
)

feeder_out_cols = [
    "timestamp_hour_ist",
    "zone",
    "locality",
    "feeder_id_hash",
    "observed_hourly_kwh",
    "observed_avg_kw",
    "feeder_capacity_kw",
    "temperature_2m_c",
    "relative_humidity_2m_pct",
    "rain_mm",
    "apparent_temperature_c",
    "weather_source_note",
    "hour",
    "day_of_week",
    "is_weekend",
    "is_holiday",
]

# Keep only columns that exist
existing_cols = [c for c in feeder_out_cols if c in feeder_hourly.columns]
feeder_out = feeder_hourly[existing_cols].copy()
feeder_out = feeder_out.sort_values(["feeder_id_hash", "timestamp_hour_ist"]).reset_index(
    drop=True
)

feeder_out["observed_hourly_kwh"] = feeder_out["observed_hourly_kwh"].round(4)
feeder_out["observed_avg_kw"] = feeder_out["observed_avg_kw"].round(4)

feeder_out.to_csv(
    OUTPUT_PATH / "feeder_hourly_energy_balance_generated.csv.gz",
    index=False,
    compression="gzip",
)

n_feeders = feeder_out["feeder_id_hash"].nunique()
logger.info(
    f"  Saved: feeder_hourly_energy_balance_generated.csv.gz "
    f"({len(feeder_out)} rows, {n_feeders} feeders)"
)


# ── STEP 6: Validate generated vs provided features ─────────────

logger.info("STEP 6 — Validating generated features against provided...")

provided_path = DATA_PATH / "model_inputs" / "meter_summary_features_from_full_interval.csv"
if provided_path.exists():
    provided = pd.read_csv(provided_path)
    generated = meter_out.copy()

    merged = generated.merge(
        provided,
        on="meter_id_hash",
        suffixes=("_gen", "_prov"),
    )

    for col in ["first30_kwh", "last30_kwh", "drop_first_to_last_pct"]:
        gen_col = f"{col}_gen"
        prov_col = f"{col}_prov"
        if gen_col in merged.columns and prov_col in merged.columns:
            gen_vals = merged[gen_col].fillna(0).values
            prov_vals = merged[prov_col].fillna(0).values
            if np.std(gen_vals) > 0 and np.std(prov_vals) > 0:
                corr = np.corrcoef(gen_vals, prov_vals)[0, 1]
                logger.info(f"  {col} correlation: {corr:.4f}")
                if corr > 0.95:
                    logger.info(f"    VALIDATED — generated features match provided")
                else:
                    logger.warning(f"    WARNING — features diverge (r={corr:.4f})")
            else:
                logger.info(f"  {col}: insufficient variance for correlation")
else:
    logger.info("  No provided features file found — skipping validation")

provided_feeder_path = DATA_PATH / "model_inputs" / "feeder_hourly_energy_balance.csv.gz"
if provided_feeder_path.exists():
    provided_feeder = pd.read_csv(provided_feeder_path, compression="gzip")
    logger.info(
        f"  Provided feeder hourly: {len(provided_feeder)} rows, "
        f"{provided_feeder['feeder_id_hash'].nunique()} feeders"
    )
    logger.info(
        f"  Generated feeder hourly: {len(feeder_out)} rows, "
        f"{n_feeders} feeders"
    )


# ── STEP 7: Final summary ───────────────────────────────────────

elapsed = time.time() - pipeline_start
logger.info("")
logger.info("=" * 60)
logger.info("M0 FEATURE ENGINEERING COMPLETE")
logger.info("=" * 60)
logger.info(f"  Source: raw_ami_mdm/matrix_parts/*.npz (4,147,200 readings)")
logger.info(f"  Meter features: {len(meter_out)} meters, {len(output_cols)} columns")
logger.info(f"  Feeder hourly: {len(feeder_out)} rows across {n_feeders} feeders")
logger.info(f"  Saved to: {OUTPUT_PATH}")
logger.info(f"  Pipeline will use generated files from model_inputs_generated/")
logger.info(f"  Total time: {elapsed:.1f}s")
logger.info("=" * 60)

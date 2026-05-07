"""
Session M1 — Anomaly Detection: Signal Engineering + Isolation Forest
Produces: anomaly_scores.csv, action_sheet.csv
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
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

gen_path = DATA_PATH / "model_inputs_generated" / "meter_summary_features_generated.csv"
provided_path = DATA_PATH / "model_inputs" / "meter_summary_features_from_full_interval.csv"
if gen_path.exists():
    meter_summary = pd.read_csv(gen_path)
    logger.info(f"  meter_summary: GENERATED ({gen_path.name})")
else:
    meter_summary = pd.read_csv(provided_path)
    logger.info(f"  meter_summary: PROVIDED fallback ({provided_path.name})")

meter_master = pd.read_csv(DATA_PATH / "raw_ami_mdm" / "05_meter_master.csv")
consumer = pd.read_csv(DATA_PATH / "raw_ami_mdm" / "06_consumer_service_point.csv")
network_gis = pd.read_csv(DATA_PATH / "raw_ami_mdm" / "07_network_gis_mapping.csv")
events = pd.read_csv(DATA_PATH / "raw_ami_mdm" / "03_meter_event_log.csv")
comm_health = pd.read_csv(DATA_PATH / "raw_ami_mdm" / "04_communication_health.csv.gz")
daily_register = pd.read_csv(DATA_PATH / "raw_ami_mdm" / "02_meter_register_daily.csv.gz")
outage_cal = pd.read_csv(DATA_PATH / "raw_ami_mdm" / "09_outage_maintenance_calendar.csv")
ground_truth = pd.read_csv(
    DATA_PATH / "synthetic_truth_and_feedback" / "anomaly_ground_truth_synthetic_only.csv"
)

for name, df in [
    ("meter_summary", meter_summary), ("meter_master", meter_master),
    ("consumer", consumer), ("network_gis", network_gis),
    ("events", events), ("comm_health", comm_health),
    ("daily_register", daily_register), ("outage_cal", outage_cal),
    ("ground_truth", ground_truth),
]:
    logger.info(f"  {name}: {df.shape}")

# ── STEP 2 — Merge base dataset ─────────────────────────────────────────────

logger.info("STEP 2 — Merging base dataset...")

merged = meter_summary.copy()

consumer_cols = [
    "service_point_id_hash", "gruha_jyothi_eligible", "net_metering_flag",
    "solar_capacity_kw", "ev_flag", "occupancy_pattern", "connection_status",
]
consumer_subset = consumer[consumer_cols].copy()
already_in = [c for c in consumer_subset.columns if c in merged.columns and c != "service_point_id_hash"]
consumer_subset = consumer_subset.drop(columns=already_in)
merged = merged.merge(consumer_subset, on="service_point_id_hash", how="left")

mm_cols = ["meter_id_hash", "meter_status", "meter_type"]
merged = merged.merge(meter_master[mm_cols], on="meter_id_hash", how="left")

gis_cols = ["meter_id_hash", "latitude_grid", "longitude_grid", "subdivision"]
gis_subset = network_gis[gis_cols].copy()
already_in = [c for c in gis_subset.columns if c in merged.columns and c != "meter_id_hash"]
gis_subset = gis_subset.drop(columns=already_in)
merged = merged.merge(gis_subset, on="meter_id_hash", how="left")

logger.info(f"  Merged: {merged.shape}")

# ── STEP 3 — Engineer 11 anomaly signals ─────────────────────────────────────

logger.info("STEP 3 — Engineering 11 anomaly signals...")

# SIGNAL 1: sig_comm_failure
comm_agg = comm_health.groupby("meter_id_hash").agg(
    avg_ping_success=("ping_success_rate", "mean"),
    total_missed=("missed_periodic_readings", "sum"),
).reset_index()
merged = merged.merge(comm_agg, on="meter_id_hash", how="left")
merged["avg_ping_success"] = merged["avg_ping_success"].fillna(1.0)
merged["total_missed"] = merged["total_missed"].fillna(0)
merged["sig_comm_failure"] = (
    (merged["avg_ping_success"] < 0.85) | (merged["total_missed"] > 30)
).astype(int)

# SIGNAL 2: sig_reading_plateau
merged["sig_reading_plateau"] = (
    merged["plateau_max_run_intervals"] >= 40
).astype(int)

# SIGNAL 3: sig_peer_drift
merged["sig_peer_drift"] = (
    merged["peer_rank_drop_points"] >= 30
).astype(int)

# SIGNAL 4: sig_sudden_drop
merged["sig_sudden_drop"] = (
    merged["drop_first_to_last_pct"] >= 40
).astype(int)

# SIGNAL 5: sig_billing_cycle_drop — compute per-cycle consumption delta
cycle_consumption = daily_register.sort_values(["meter_id_hash", "billing_cycle_id", "read_date"])
cycle_edges = cycle_consumption.groupby(["meter_id_hash", "billing_cycle_id"])["cum_import_kwh"].agg(
    cycle_start="first", cycle_end="last"
).reset_index()
cycle_edges["cycle_kwh"] = cycle_edges["cycle_end"] - cycle_edges["cycle_start"]
cycle_edges["cycle_kwh"] = cycle_edges["cycle_kwh"].clip(lower=0)

first_cycle = cycle_edges.groupby("meter_id_hash").first()[["cycle_kwh"]].rename(
    columns={"cycle_kwh": "first_cycle_kwh"}
)
last_cycle = cycle_edges.groupby("meter_id_hash").last()[["cycle_kwh"]].rename(
    columns={"cycle_kwh": "last_cycle_kwh"}
)
billing_df = first_cycle.merge(last_cycle, left_index=True, right_index=True).reset_index()
billing_df["sig_billing_cycle_drop"] = (
    (billing_df["first_cycle_kwh"] > 10)
    & (billing_df["last_cycle_kwh"] < billing_df["first_cycle_kwh"] * 0.5)
).astype(int)
merged = merged.merge(
    billing_df[["meter_id_hash", "sig_billing_cycle_drop"]], on="meter_id_hash", how="left"
)
merged["sig_billing_cycle_drop"] = merged["sig_billing_cycle_drop"].fillna(0).astype(int)

# SIGNAL 6: sig_after_hours_commercial
merged["sig_after_hours_commercial"] = (
    (merged["consumer_category"] == "COMMERCIAL") & (merged["after_hours_ratio"] > 1.5)
).astype(int)

# SIGNAL 7: sig_pf_register
merged["sig_pf_register"] = (
    merged["min_power_factor"] < 0.85
).astype(int)

# SIGNAL 8: sig_tamper_event
event_tamper = events[
    (events["event_type"].str.contains("TAMPER|COVER_OPEN|MAGNETIC", case=False, na=False))
    | (events["event_severity"] == "HIGH")
].groupby("meter_id_hash").size().reset_index(name="tamper_event_count")
merged = merged.merge(event_tamper, on="meter_id_hash", how="left")
merged["tamper_event_count"] = merged["tamper_event_count"].fillna(0).astype(int)

tamper_daily = daily_register.groupby("meter_id_hash")["tamper_count_daily"].sum().reset_index(
    name="total_tamper_daily"
)
merged = merged.merge(tamper_daily, on="meter_id_hash", how="left")
merged["total_tamper_daily"] = merged["total_tamper_daily"].fillna(0).astype(int)

merged["sig_tamper_event"] = (
    (merged["tamper_event_count"] >= 2) | (merged["total_tamper_daily"] >= 3)
).astype(int)

# SIGNAL 9: sig_genuine_low_usage_context (SUPPRESSOR)
merged["sig_genuine_low_usage_context"] = (
    (merged["gruha_jyothi_eligible"] == 1)
    & (merged["last30_kwh"] < merged["monthly_baseline_units"] * 1.2)
).astype(int)

# SIGNAL 10: sig_solar_export_normal (SUPPRESSOR)
merged["sig_solar_export_normal"] = (
    (merged["solar_capacity_kw"] > 0) & (merged["net_metering_flag"] == 1)
).astype(int)

# SIGNAL 11: sig_ev_consistent_night_pattern (SUPPRESSOR)
merged["sig_ev_consistent_night_pattern"] = (
    merged["ev_flag"] == 1
).astype(int)

signal_cols = [
    "sig_comm_failure", "sig_reading_plateau", "sig_peer_drift",
    "sig_sudden_drop", "sig_billing_cycle_drop", "sig_after_hours_commercial",
    "sig_pf_register", "sig_tamper_event",
    "sig_genuine_low_usage_context", "sig_solar_export_normal",
    "sig_ev_consistent_night_pattern",
]
logger.info("  Signal trigger counts:")
for col in signal_cols:
    logger.info(f"    {col}: {merged[col].sum()}")

# ── STEP 4 — Inactive meter suppression ─────────────────────────────────────

logger.info("STEP 4 — Inactive meter suppression...")

inactive_statuses = [
    "SUSPENDED_NON_PAYMENT", "DISCONNECTED_OWNER_REQUEST",
    "TEMPORARILY_DISCONNECTED_THEFT_SUSPECTED", "DISPUTED_BILLING",
    "DECOMMISSIONED",
]
merged["is_active_meter"] = (~merged["meter_status"].isin(inactive_statuses)).astype(int)
inactive_count = (merged["is_active_meter"] == 0).sum()
active_count = (merged["is_active_meter"] == 1).sum()
logger.info(f"  Active: {active_count}, Inactive: {inactive_count}")

for col in signal_cols:
    merged.loc[merged["is_active_meter"] == 0, col] = 0

# ── STEP 5 — Outage overlap suppression ─────────────────────────────────────

logger.info("STEP 5 — Outage overlap suppression...")

outage_localities = set(outage_cal["locality"].unique())
merged["outage_suppressed"] = 0
outage_mask = (
    merged["locality"].isin(outage_localities) & (merged["sig_sudden_drop"] == 1)
)
merged.loc[outage_mask, "sig_sudden_drop"] = 0
merged.loc[outage_mask, "outage_suppressed"] = 1
logger.info(f"  Outage-suppressed sudden drops: {outage_mask.sum()}")

# ── STEP 6 — Isolation Forest scoring ───────────────────────────────────────

logger.info("STEP 6 — Isolation Forest scoring...")

features = [
    "drop_first_to_last_pct", "drop_prev_to_last_pct",
    "missing_pct", "after_hours_ratio", "avg_power_factor",
    "min_power_factor", "plateau_max_run_intervals",
    "peer_rank_drop_points", "first30_kwh", "last30_kwh",
]

active_mask = merged["is_active_meter"] == 1
X_raw = merged.loc[active_mask, features].fillna(0)

scaler = StandardScaler()
X = scaler.fit_transform(X_raw)

iso_forest = IsolationForest(
    n_estimators=200, contamination=0.12, random_state=42, n_jobs=-1
)
iso_forest.fit(X)
scores = iso_forest.decision_function(X)

score_min, score_max = scores.min(), scores.max()
if score_max > score_min:
    iso_scores_norm = (1 - (scores - score_min) / (score_max - score_min)) * 100
else:
    iso_scores_norm = np.full_like(scores, 50.0)

merged["isolation_forest_score"] = 0.0
merged.loc[active_mask, "isolation_forest_score"] = iso_scores_norm

logger.info(f"  IF scores: mean={merged['isolation_forest_score'].mean():.1f}, "
            f"median={merged['isolation_forest_score'].median():.1f}, "
            f"max={merged['isolation_forest_score'].max():.1f}")

# ── STEP 7 — Cluster watchlist boost ────────────────────────────────────────

logger.info("STEP 7 — Cluster watchlist boost...")

# Strong signals are direct indicators of theft/loss
STRONG_SIGNALS = [
    "sig_peer_drift", "sig_sudden_drop", "sig_billing_cycle_drop",
    "sig_tamper_event", "sig_after_hours_commercial",
]
# Weak signals are supporting evidence (useful in combination, noisy alone)
WEAK_SIGNALS = [
    "sig_comm_failure", "sig_reading_plateau", "sig_pf_register",
]
DETECTOR_COLS = STRONG_SIGNALS + WEAK_SIGNALS

dt_has_alert = merged.groupby("dt_id_hash").apply(
    lambda g: ((g["sig_peer_drift"] == 1) | (g["sig_sudden_drop"] == 1)).any()
).reset_index(name="dt_has_anomaly")

merged = merged.merge(dt_has_alert, on="dt_id_hash", how="left")
merged["dt_has_anomaly"] = merged["dt_has_anomaly"].fillna(False)

merged["any_signal"] = merged[DETECTOR_COLS].sum(axis=1) > 0
merged["cluster_watchlist_boost"] = (
    merged["dt_has_anomaly"] & merged["any_signal"]
    & (merged["is_active_meter"] == 1)
).astype(int)

logger.info(f"  Cluster-boosted meters: {merged['cluster_watchlist_boost'].sum()}")
merged.drop(columns=["dt_has_anomaly", "any_signal"], inplace=True)

# ── STEP 8 — Composite risk score ───────────────────────────────────────────

logger.info("STEP 8 — Computing composite risk score...")

merged["strong_signal_count"] = merged[STRONG_SIGNALS].sum(axis=1)
merged["weak_signal_count"] = merged[WEAK_SIGNALS].sum(axis=1)
merged["independent_signal_count"] = merged[DETECTOR_COLS].sum(axis=1)

suppressor_cols = [
    "sig_genuine_low_usage_context", "sig_solar_export_normal",
    "sig_ev_consistent_night_pattern",
]
merged["suppressor_count"] = merged[suppressor_cols].sum(axis=1)

merged["risk_score"] = (
    merged["isolation_forest_score"] * 0.3
    + merged["strong_signal_count"] * 18
    + merged["weak_signal_count"] * 8
    + merged["cluster_watchlist_boost"] * 5
    - merged["suppressor_count"] * 20
)
merged["risk_score"] = merged["risk_score"].clip(0, 100)

# ── STEP 9 — Assign risk tiers ──────────────────────────────────────────────

logger.info("STEP 9 — Assigning risk tiers...")


def assign_tier(row):
    if row["is_active_meter"] == 0:
        return "INACTIVE_SUPPRESSED", None

    strong = row["strong_signal_count"]
    weak = row["weak_signal_count"]
    total = row["independent_signal_count"]
    supp = row["suppressor_count"]
    iso = row["isolation_forest_score"]

    if supp > 0 and strong == 0 and total <= 1:
        if row["sig_genuine_low_usage_context"] == 1:
            return "FALSE_POSITIVE_PREVENTED_GJ", None
        elif row["sig_solar_export_normal"] == 1:
            return "SOLAR_CONTEXT_SUPPRESSED", None
        elif row["sig_ev_consistent_night_pattern"] == 1:
            return "EV_CONTEXT_SUPPRESSED", None

    if strong >= 2:
        return "MULTI_SIGNAL_CONFIRMED", "P1"

    if strong >= 1 and weak >= 1:
        return "MULTI_SIGNAL_CONFIRMED", "P1"

    if strong == 1 and iso >= 60:
        return "SINGLE_SIGNAL_PROBABLE", "P2"

    if strong == 1:
        return "SINGLE_SIGNAL_REVIEW", "P2"

    # Weak signals alone only flag if Isolation Forest also agrees
    if weak >= 2 and iso >= 65:
        return "SINGLE_SIGNAL_REVIEW", "P2"

    if row["cluster_watchlist_boost"] == 1 and total >= 1:
        return "CLUSTER_WATCHLIST", "P3"

    if iso >= 75 and total == 0:
        return "STATISTICAL_OUTLIER_ONLY", "P3"

    return "NO_ALERT", None


tier_results = merged.apply(assign_tier, axis=1, result_type="expand")
merged["risk_tier"] = tier_results[0]
merged["priority"] = tier_results[1]

for tier in merged["risk_tier"].value_counts().index:
    count = (merged["risk_tier"] == tier).sum()
    logger.info(f"  {tier}: {count}")

# ── STEP 10 — Assign recommended teams ──────────────────────────────────────

logger.info("STEP 10 — Assigning recommended teams...")

theft_signals = {"sig_peer_drift", "sig_sudden_drop", "sig_billing_cycle_drop", "sig_tamper_event"}


def assign_team(row):
    if row["priority"] is None:
        return None
    for sig in theft_signals:
        if row.get(sig, 0) == 1:
            return "Vigilance"
    if row["sig_comm_failure"] == 1:
        return "IT/AMI"
    if row["sig_reading_plateau"] == 1:
        return "Metering"
    if row["sig_after_hours_commercial"] == 1:
        return "Vigilance"
    if row["sig_pf_register"] == 1:
        return "Metering"
    return "O&M"


merged["recommended_team"] = merged.apply(assign_team, axis=1)

# ── STEP 11 — Alert fingerprint and action ──────────────────────────────────

logger.info("STEP 11 — Generating alert fingerprints and actions...")

signal_labels = {
    "sig_comm_failure": "Communication Failure",
    "sig_reading_plateau": "Reading Plateau",
    "sig_peer_drift": "Peer Drift",
    "sig_sudden_drop": "Sudden Drop",
    "sig_billing_cycle_drop": "Billing Cycle Drop",
    "sig_after_hours_commercial": "After-Hours Commercial",
    "sig_pf_register": "Low Power Factor",
    "sig_tamper_event": "Tamper Event",
}

team_actions = {
    "Vigilance": "Schedule vigilance inspection within 7 days",
    "IT/AMI": "Verify communication module and data pipeline",
    "Metering": "Schedule meter health check",
    "O&M": "Monitor feeder loading and schedule maintenance",
}


def build_fingerprint(row):
    triggered = [label for sig, label in signal_labels.items() if row.get(sig, 0) == 1]
    return " + ".join(triggered) if triggered else None


def build_action(row):
    if row["recommended_team"] is None:
        return None
    return team_actions.get(row["recommended_team"], "Review case")


def build_one_liner(row):
    if row["priority"] is None:
        return None
    parts = []
    cat = row.get("consumer_category", "")
    loc = row.get("locality", "")
    sub = row.get("premise_subtype", "")
    parts.append(f"{sub} {loc} {cat} meter".strip())
    drop = row.get("drop_first_to_last_pct", 0)
    if drop and drop > 0:
        parts.append(f"dropped {drop:.0f}% consumption")
    pr_drop = row.get("peer_rank_drop_points", 0)
    if pr_drop and pr_drop > 0:
        parts.append(f"{pr_drop:.0f}-pt peer rank drop")
    tc = row.get("tamper_event_count", 0)
    if tc and tc > 0:
        parts.append(f"{int(tc)} tamper events")
    return ", ".join(parts)


merged["alert_fingerprint"] = merged.apply(build_fingerprint, axis=1)
merged["recommended_action"] = merged.apply(build_action, axis=1)
merged["one_line_reason"] = merged.apply(build_one_liner, axis=1)

# ── STEP 12 — Revenue impact ────────────────────────────────────────────────

logger.info("STEP 12 — Estimating revenue impact...")

tariff_rates = {
    "RESIDENTIAL": 6.0,
    "COMMERCIAL": 8.0,
    "SMALL_INDUSTRY": 7.0,
    "APARTMENT_COMMON_AREA": 6.0,
    "PUBLIC_LIGHTING": 6.0,
}

merged["tariff_rate"] = merged["consumer_category"].map(tariff_rates).fillna(6.0)
merged["monthly_loss_kwh"] = (merged["first30_kwh"] - merged["last30_kwh"]).clip(lower=0)
merged["estimated_revenue_impact_inr"] = np.where(
    merged["priority"].isin(["P1", "P2"]),
    merged["monthly_loss_kwh"] * merged["tariff_rate"],
    0.0,
)
merged["estimated_revenue_impact_inr"] = merged["estimated_revenue_impact_inr"].round(2)

total_rev = merged["estimated_revenue_impact_inr"].sum()
logger.info(f"  Total monthly revenue at risk: Rs.{total_rev:,.0f}")

# ── STEP 13 — Confidence percentage ─────────────────────────────────────────

logger.info("STEP 13 — Computing confidence percentages...")

merged["confidence_pct"] = (
    merged["strong_signal_count"] * 22
    + merged["weak_signal_count"] * 8
    + merged["isolation_forest_score"] * 0.3
    + merged["cluster_watchlist_boost"] * 5
).clip(10, 99).round(1)

merged.loc[merged["priority"].isna(), "confidence_pct"] = np.nan

# ── STEP 14 — Save anomaly_scores.csv ───────────────────────────────────────

logger.info("STEP 14 — Saving anomaly_scores.csv...")

output_cols = [
    "meter_id_hash", "service_point_id_hash", "locality", "zone",
    "feeder_id_hash", "dt_id_hash", "consumer_category", "premise_subtype",
    "latitude_grid", "longitude_grid",
    "sig_comm_failure", "sig_reading_plateau", "sig_peer_drift",
    "sig_sudden_drop", "sig_billing_cycle_drop",
    "sig_after_hours_commercial", "sig_pf_register", "sig_tamper_event",
    "sig_genuine_low_usage_context", "sig_solar_export_normal",
    "sig_ev_consistent_night_pattern",
    "isolation_forest_score", "cluster_watchlist_boost",
    "independent_signal_count", "suppressor_count",
    "risk_score", "risk_tier", "priority",
    "recommended_team", "recommended_action", "alert_fingerprint",
    "one_line_reason", "confidence_pct",
    "estimated_revenue_impact_inr", "is_active_meter",
]

anomaly_scores = merged[output_cols].copy()
anomaly_scores.to_csv(OUTPUT_PATH / "anomaly_scores.csv", index=False)

p1 = (anomaly_scores["priority"] == "P1").sum()
p2 = (anomaly_scores["priority"] == "P2").sum()
p3 = (anomaly_scores["priority"] == "P3").sum()
suppressed_inactive = (anomaly_scores["risk_tier"] == "INACTIVE_SUPPRESSED").sum()
suppressed_context = anomaly_scores["risk_tier"].isin([
    "FALSE_POSITIVE_PREVENTED_GJ", "SOLAR_CONTEXT_SUPPRESSED", "EV_CONTEXT_SUPPRESSED"
]).sum()
no_alert = (anomaly_scores["risk_tier"] == "NO_ALERT").sum()

logger.info(f"  Total meters: {len(anomaly_scores)}")
logger.info(f"  Active: {active_count}")
logger.info(f"  P1 cases: {p1}")
logger.info(f"  P2 cases: {p2}")
logger.info(f"  P3 cases: {p3}")
logger.info(f"  Suppressed (inactive): {suppressed_inactive}")
logger.info(f"  Suppressed (GJ/solar/EV): {suppressed_context}")
logger.info(f"  No alert: {no_alert}")

# ── STEP 15 — Generate action_sheet.csv ──────────────────────────────────────

logger.info("STEP 15 — Generating action_sheet.csv...")

action_df = anomaly_scores[anomaly_scores["priority"].notna()].copy()
action_df = action_df.sort_values(
    ["priority", "confidence_pct"], ascending=[True, False]
).reset_index(drop=True)

action_df["case_id"] = [f"ALT-V4-{i+1:04d}" for i in range(len(action_df))]

team_to_case_type = {
    "Vigilance": "ANOMALY_THEFT",
    "IT/AMI": "COMMUNICATION",
    "Metering": "METER_HEALTH",
    "O&M": "GRID_STRESS",
}
action_df["case_type"] = action_df["recommended_team"].map(team_to_case_type).fillna("OTHER")

action_cols = [
    "case_id", "case_type", "priority", "meter_id_hash",
    "service_point_id_hash", "locality", "zone", "feeder_id_hash",
    "dt_id_hash", "consumer_category", "premise_subtype",
    "alert_fingerprint", "confidence_pct", "risk_tier",
    "recommended_team", "recommended_action",
    "estimated_revenue_impact_inr", "risk_score",
    "independent_signal_count", "one_line_reason",
]

action_sheet = action_df[action_cols]
action_sheet.to_csv(OUTPUT_PATH / "action_sheet.csv", index=False)

ap1 = (action_sheet["priority"] == "P1").sum()
ap2 = (action_sheet["priority"] == "P2").sum()
ap3 = (action_sheet["priority"] == "P3").sum()
logger.info(f"  Action sheet: {len(action_sheet)} cases (P1={ap1}, P2={ap2}, P3={ap3})")

# ── STEP 16 — Validate against ground truth ─────────────────────────────────

logger.info("STEP 16 — Validating against ground truth...")

val = anomaly_scores.merge(ground_truth[["meter_id_hash", "is_suspicious_truth", "primary_label"]],
                           on="meter_id_hash", how="left")

flagged = val["priority"].notna()
suspicious = val["is_suspicious_truth"] == 1

tp = (flagged & suspicious).sum()
fp = (flagged & ~suspicious).sum()
tn = (~flagged & ~suspicious).sum()
fn = (~flagged & suspicious).sum()

precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

logger.info(f"  Confusion matrix: TP={tp}, FP={fp}, TN={tn}, FN={fn}")
logger.info(f"  Precision: {precision:.3f}")
logger.info(f"  Recall: {recall:.3f}")
logger.info(f"  F1: {f1:.3f}")

inactive_match = (
    (val["risk_tier"] == "INACTIVE_SUPPRESSED")
    & val["primary_label"].str.contains("inactive", case=False, na=False)
).sum()
inactive_total = val["primary_label"].str.contains("inactive", case=False, na=False).sum()
logger.info(f"  Inactive suppression matched ground truth: {inactive_match}/{inactive_total}")

gj_solar_ev_suppressed = val["risk_tier"].isin([
    "FALSE_POSITIVE_PREVENTED_GJ", "SOLAR_CONTEXT_SUPPRESSED", "EV_CONTEXT_SUPPRESSED"
]).sum()
gj_solar_ev_truth = val["primary_label"].isin([
    "normal_low_usage_gruha_jyothi_suppressed", "solar_daytime_low_import_non_suspicious",
    "ev_night_charging_normal"
]).sum()
logger.info(f"  GJ/solar/EV suppression: {gj_solar_ev_suppressed} suppressed "
            f"(ground truth has {gj_solar_ev_truth} context meters)")

elapsed = time.time() - start_time
logger.info("")
logger.info("=" * 60)
logger.info("M1 ANOMALY DETECTION COMPLETE")
logger.info("=" * 60)
logger.info(f"  anomaly_scores.csv: {len(anomaly_scores)} rows")
logger.info(f"  action_sheet.csv: {len(action_sheet)} cases")
logger.info(f"  Total time: {elapsed:.1f}s")
logger.info("=" * 60)

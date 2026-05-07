import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import os
import time
import logging

load_dotenv()
logger = logging.getLogger(__name__)

DATA_PATH = Path(os.environ.get("DATA_BASE_PATH", "./data"))

_cache: dict[str, pd.DataFrame] = {}

FILE_REGISTRY: dict[str, dict] = {
    "anomaly_scores": {"path": "model_outputs/anomaly_scores.csv"},
    "action_sheet": {"path": "model_outputs/action_sheet.csv"},
    "evidence_cards": {"path": "model_outputs/evidence_cards.csv"},
    "demand_forecast": {"path": "model_outputs/demand_forecast_and_baselines.csv.gz"},
    "grid_stress": {"path": "model_outputs/grid_stress_risk_bands.csv"},
    "baseline_results": {"path": "model_outputs/baseline_results.csv"},
    "feature_importance": {"path": "model_outputs/forecast_feature_importance.csv"},
    "revenue_impact": {"path": "model_outputs/revenue_impact_estimate.csv"},
    "false_positive_audit": {"path": "model_outputs/false_positive_audit.csv"},
    "fp_rate_by_signal": {"path": "model_outputs/false_positive_rate_by_signal.csv"},
    "evaluation_results": {"path": "model_outputs/anomaly_evaluation_results.csv"},
    "kpi_summary": {"path": "model_outputs/subdivision_kpi_summary.csv"},
    "threshold_log": {"path": "model_outputs/threshold_recalibration_log.csv"},
    "demo_cases": {"path": "model_outputs/demo_story_cases.csv"},
    "meter_summary": {
        "path": "model_inputs_generated/meter_summary_features_generated.csv",
        "fallback": "model_inputs/meter_summary_features_from_full_interval.csv",
    },
    "feeder_hourly": {
        "path": "model_inputs_generated/feeder_hourly_energy_balance_generated.csv.gz",
        "fallback": "model_inputs/feeder_hourly_energy_balance.csv.gz",
    },
    "locality_features": {"path": "model_inputs/hourly_feeder_locality_features.csv.gz"},
    "meter_master": {"path": "raw_ami_mdm/05_meter_master.csv"},
    "consumer": {"path": "raw_ami_mdm/06_consumer_service_point.csv"},
    "network_gis": {"path": "raw_ami_mdm/07_network_gis_mapping.csv"},
    "events": {"path": "raw_ami_mdm/03_meter_event_log.csv"},
    "comm_health": {"path": "raw_ami_mdm/04_communication_health.csv.gz"},
    "daily_register": {"path": "raw_ami_mdm/02_meter_register_daily.csv.gz"},
    "outage_calendar": {"path": "raw_ami_mdm/09_outage_maintenance_calendar.csv"},
    "capacity": {"path": "raw_ami_mdm/08_feeder_dt_capacity.csv"},
    "matrix_index": {"path": "raw_ami_mdm/01_meter_interval_matrix_index.csv"},
    "feeder_system": {"path": "raw_ami_mdm/10_system_meter_interval_15min_feeder_sample.csv.gz"},
    "dt_system": {"path": "raw_ami_mdm/11_system_meter_interval_15min_dt_sample.csv.gz"},
    "weather": {"path": "external_enrichment/weather_bengaluru_hourly.csv"},
    "holidays": {"path": "external_enrichment/holiday_festival_calendar.csv"},
    "tariff": {"path": "external_enrichment/tariff_policy_reference.csv"},
    "ground_truth": {"path": "synthetic_truth_and_feedback/anomaly_ground_truth_synthetic_only.csv"},
    "feedback_sim": {"path": "synthetic_truth_and_feedback/inspection_feedback_simulated.csv"},
}


def _load(key: str) -> pd.DataFrame:
    if key in _cache:
        return _cache[key]

    entry = FILE_REGISTRY[key]
    primary = DATA_PATH / entry["path"]
    fallback = DATA_PATH / entry["fallback"] if "fallback" in entry else None

    if primary.exists():
        df = pd.read_csv(primary)
    elif fallback and fallback.exists():
        df = pd.read_csv(fallback)
        logger.info(f"  {key}: using fallback {fallback.name}")
    else:
        logger.warning(f"  {key}: file not found at {primary}")
        return pd.DataFrame()

    _cache[key] = df
    return df


def load_all_data() -> dict:
    start = time.time()
    files_loaded = 0
    total_records = 0
    errors = []

    for key in FILE_REGISTRY:
        try:
            df = _load(key)
            if not df.empty:
                files_loaded += 1
                total_records += len(df)
        except Exception as e:
            errors.append(f"{key}: {e}")

    elapsed = time.time() - start
    return {
        "files_loaded": files_loaded,
        "total_files": len(FILE_REGISTRY),
        "total_records": total_records,
        "load_time_seconds": round(elapsed, 2),
        "errors": errors,
    }


def clear_cache():
    _cache.clear()


def get_anomaly_scores() -> pd.DataFrame:
    return _load("anomaly_scores")

def get_action_sheet() -> pd.DataFrame:
    return _load("action_sheet")

def get_evidence_cards() -> pd.DataFrame:
    return _load("evidence_cards")

def get_demand_forecast() -> pd.DataFrame:
    return _load("demand_forecast")

def get_grid_stress() -> pd.DataFrame:
    return _load("grid_stress")

def get_baseline_results() -> pd.DataFrame:
    return _load("baseline_results")

def get_feature_importance() -> pd.DataFrame:
    return _load("feature_importance")

def get_revenue_impact() -> pd.DataFrame:
    return _load("revenue_impact")

def get_false_positive_audit() -> pd.DataFrame:
    return _load("false_positive_audit")

def get_fp_rate_by_signal() -> pd.DataFrame:
    return _load("fp_rate_by_signal")

def get_evaluation_results() -> pd.DataFrame:
    return _load("evaluation_results")

def get_kpi_summary() -> pd.DataFrame:
    return _load("kpi_summary")

def get_threshold_log() -> pd.DataFrame:
    return _load("threshold_log")

def get_demo_cases() -> pd.DataFrame:
    return _load("demo_cases")

def get_meter_summary() -> pd.DataFrame:
    return _load("meter_summary")

def get_feeder_hourly() -> pd.DataFrame:
    return _load("feeder_hourly")

def get_locality_features() -> pd.DataFrame:
    return _load("locality_features")

def get_meter_master() -> pd.DataFrame:
    return _load("meter_master")

def get_consumer() -> pd.DataFrame:
    return _load("consumer")

def get_network_gis() -> pd.DataFrame:
    return _load("network_gis")

def get_events() -> pd.DataFrame:
    return _load("events")

def get_comm_health() -> pd.DataFrame:
    return _load("comm_health")

def get_daily_register() -> pd.DataFrame:
    return _load("daily_register")

def get_outage_calendar() -> pd.DataFrame:
    return _load("outage_calendar")

def get_capacity() -> pd.DataFrame:
    return _load("capacity")

def get_matrix_index() -> pd.DataFrame:
    return _load("matrix_index")

def get_feeder_system() -> pd.DataFrame:
    return _load("feeder_system")

def get_dt_system() -> pd.DataFrame:
    return _load("dt_system")

def get_weather() -> pd.DataFrame:
    return _load("weather")

def get_holidays() -> pd.DataFrame:
    return _load("holidays")

def get_tariff() -> pd.DataFrame:
    return _load("tariff")

def get_ground_truth() -> pd.DataFrame:
    return _load("ground_truth")

def get_feedback_sim() -> pd.DataFrame:
    return _load("feedback_sim")

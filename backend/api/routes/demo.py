from fastapi import APIRouter
from services import data_loader
from services import legal_trail_service
from utils.helpers import df_to_records
from utils.nan_cleaner import clean_for_json

router = APIRouter(prefix="/api/demo", tags=["Demo"])


@router.get("/cases")
def demo_cases():
    return clean_for_json(df_to_records(data_loader.get_demo_cases()))


@router.get("/audit-trail/{case_id}")
def audit_trail(case_id: str):
    result = legal_trail_service.get_audit_trail(case_id)
    if result is None:
        return {"error": "Case not found"}
    return result


@router.get("/pipeline-summary")
def pipeline_summary():
    scores = data_loader.get_anomaly_scores()
    action = data_loader.get_action_sheet()
    baseline = data_loader.get_baseline_results()
    grid = data_loader.get_grid_stress()
    evidence = data_loader.get_evidence_cards()
    revenue = data_loader.get_revenue_impact()

    our = baseline[baseline["model_or_baseline"] == "Aletheon_LightGBM"]

    agg = revenue[revenue["case_id"] == "AGGREGATE_PILOT_SUBDIVISION"]
    monthly_loss = agg["monthly_loss_inr_high"].values[0] if len(agg) > 0 else 0

    return clean_for_json({
        "anomaly_detection": {
            "total_meters": len(scores),
            "active_meters": int((scores["is_active_meter"] == 1).sum()),
            "p1_cases": int((action["priority"] == "P1").sum()),
            "p2_cases": int((action["priority"] == "P2").sum()),
            "p3_cases": int((action["priority"] == "P3").sum()),
            "evidence_cards": len(evidence),
        },
        "demand_forecast": {
            "wmape_pct": float(our.iloc[0]["WMAPE_pct"]) if len(our) > 0 else None,
            "mae_kwh": float(our.iloc[0]["MAE_kWh"]) if len(our) > 0 else None,
        },
        "grid_stress": {
            "red_feeders": int((grid["grid_risk_band"] == "RED").sum()),
            "amber_feeders": int((grid["grid_risk_band"] == "AMBER").sum()),
            "green_feeders": int((grid["grid_risk_band"] == "GREEN").sum()),
        },
        "revenue_at_risk_monthly_inr": float(monthly_loss),
    })


@router.get("/data-health")
def data_health():
    summary = data_loader.load_all_data()
    return summary

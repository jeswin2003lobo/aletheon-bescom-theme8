from fastapi import APIRouter, Query
from services import forecast_service

router = APIRouter(prefix="/api/forecast", tags=["Forecast"])


@router.get("/overview")
def forecast_overview():
    return forecast_service.get_forecast_overview()


@router.get("/feeder/{feeder_id}")
def forecast_by_feeder(feeder_id: str, test_only: bool = Query(False)):
    result = forecast_service.get_forecast_by_feeder(feeder_id, test_only=test_only)
    if result is None:
        return {"error": "Feeder not found"}
    return result


@router.get("/timeseries")
def forecast_timeseries(
    feeder_id: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=2000),
):
    return forecast_service.get_forecast_timeseries(feeder_id=feeder_id, page=page, page_size=page_size)


@router.get("/baselines")
def baseline_comparison():
    return forecast_service.get_baseline_comparison()


@router.get("/feature-importance")
def feature_importance():
    return forecast_service.get_feature_importance()


@router.get("/demand-alerts")
def demand_alerts():
    return forecast_service.get_demand_alerts()

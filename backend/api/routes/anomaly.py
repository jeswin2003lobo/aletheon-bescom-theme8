from fastapi import APIRouter, Query
from services import anomaly_service

router = APIRouter(prefix="/api/anomaly", tags=["Anomaly"])


@router.get("/overview")
def anomaly_overview():
    return anomaly_service.get_anomaly_overview()


@router.get("/scores")
def anomaly_scores(
    zone: str = Query(None),
    locality: str = Query(None),
    priority: str = Query(None),
    risk_tier: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
):
    return anomaly_service.get_anomaly_scores(
        zone=zone, locality=locality, priority=priority,
        risk_tier=risk_tier, page=page, page_size=page_size,
    )


@router.get("/scores/{meter_id}")
def meter_anomaly(meter_id: str):
    result = anomaly_service.get_meter_anomaly(meter_id)
    if result is None:
        return {"error": "Meter not found"}
    return result


@router.get("/action-sheet")
def action_sheet(
    priority: str = Query(None),
    team: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
):
    return anomaly_service.get_action_sheet(priority=priority, team=team, page=page, page_size=page_size)


@router.get("/action-sheet/{case_id}")
def action_by_case(case_id: str):
    result = anomaly_service.get_action_by_case(case_id)
    if result is None:
        return {"error": "Case not found"}
    return result


@router.get("/signals")
def signal_summary():
    return anomaly_service.get_signal_summary()

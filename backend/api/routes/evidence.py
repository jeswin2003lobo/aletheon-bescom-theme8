from fastapi import APIRouter, Query
from services import evidence_service

router = APIRouter(prefix="/api/evidence", tags=["Evidence"])


@router.get("/cards")
def evidence_cards(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return evidence_service.get_evidence_cards(page=page, page_size=page_size)


@router.get("/cards/{case_id}")
def evidence_by_case(case_id: str):
    result = evidence_service.get_evidence_by_case(case_id)
    if result is None:
        return {"error": "Case not found"}
    return result


@router.get("/meter/{meter_id}")
def evidence_by_meter(meter_id: str):
    result = evidence_service.get_evidence_by_meter(meter_id)
    if result is None:
        return {"error": "No evidence for meter"}
    return result

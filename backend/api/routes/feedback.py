from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from services import feedback_service

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


class FeedbackSubmit(BaseModel):
    case_id: str
    meter_id_hash: str
    feedback_type: str
    finding: str
    inspector_id: Optional[str] = None
    notes: Optional[str] = None
    photo_reference: Optional[str] = None


@router.post("/submit")
def submit_feedback(req: FeedbackSubmit):
    return feedback_service.submit_feedback(
        case_id=req.case_id,
        meter_id_hash=req.meter_id_hash,
        feedback_type=req.feedback_type,
        finding=req.finding,
        inspector_id=req.inspector_id,
        notes=req.notes,
        photo_reference=req.photo_reference,
    )


@router.get("/list")
def list_feedback(
    case_id: str = Query(None),
    meter_id: str = Query(None),
):
    return feedback_service.get_feedback(case_id=case_id, meter_id=meter_id)


@router.get("/stats")
def feedback_stats():
    return feedback_service.get_feedback_stats()

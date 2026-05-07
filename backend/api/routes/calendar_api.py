from fastapi import APIRouter, Query
from services import calendar_service

router = APIRouter(prefix="/api/calendar", tags=["Calendar"])


@router.get("/holidays")
async def get_holidays(
    year: str = Query(None),
    month: int = Query(None, ge=1, le=12),
):
    return await calendar_service.get_holidays(year=year, month=month)

from fastapi import APIRouter, Query
from services import grid_service

router = APIRouter(prefix="/api/grid", tags=["Grid"])


@router.get("/overview")
def grid_overview():
    return grid_service.get_grid_overview()


@router.get("/stress")
def grid_stress_list(
    zone: str = Query(None),
    band: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
):
    return grid_service.get_grid_stress_list(zone=zone, band=band, page=page, page_size=page_size)


@router.get("/stress/{feeder_id}")
def grid_stress_by_feeder(feeder_id: str):
    result = grid_service.get_grid_stress_by_feeder(feeder_id)
    if result is None:
        return {"error": "Feeder not found"}
    return result

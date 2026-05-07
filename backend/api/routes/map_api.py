from fastapi import APIRouter, Query
from services import map_service

router = APIRouter(prefix="/api/map", tags=["Map"])


@router.get("/meters")
def meter_map(
    zone: str = Query(None),
    locality: str = Query(None),
    priority: str = Query(None),
):
    return map_service.get_meter_map_data(zone=zone, locality=locality, priority=priority)


@router.get("/feeders")
def feeder_map():
    return map_service.get_feeder_map_data()


@router.get("/dts")
def dt_map(feeder_id: str = Query(None)):
    return map_service.get_dt_map_data(feeder_id=feeder_id)

from fastapi import APIRouter
from pydantic import BaseModel
from services import sms_service

router = APIRouter(prefix="/api/notify", tags=["Notify"])


class SMSRequest(BaseModel):
    message: str
    phone_numbers: str = None


class AlertRequest(BaseModel):
    case_id: str
    meter_id: str
    priority: str
    reason: str


@router.post("/sms")
async def send_sms(req: SMSRequest):
    return await sms_service.send_sms(req.message, req.phone_numbers)


@router.post("/alert")
async def send_alert(req: AlertRequest):
    return await sms_service.send_alert(req.case_id, req.meter_id, req.priority, req.reason)

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.firebase import send_fcm_notification

router = APIRouter()

class AlertRequest(BaseModel):
    token: str
    title: str
    body: str
    data: Optional[dict] = None

@router.post("/send")
async def send_alert(req: AlertRequest):
    message_id = send_fcm_notification(req.token, req.title, req.body, req.data)
    return {"success": True, "message_id": message_id}

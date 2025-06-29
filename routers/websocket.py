from fastapi import APIRouter, WebSocket
from app.services.audio_proxy import AudioProxy

router = APIRouter()
proxy = AudioProxy()

@router.websocket("/realtime")
async def realtime(ws: WebSocket):
    await proxy.websocket_proxy(ws)

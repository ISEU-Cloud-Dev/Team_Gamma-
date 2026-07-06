from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.connection_manager import manager

router = APIRouter()

@router.websocket("/ws/surveys/{survey_id}")
async def websocket_endpoint(websocket: WebSocket, survey_id: int):
    await manager.connect(websocket, survey_id)
    try:
        await websocket.send_json({"event": "connected", "survey_id": survey_id})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, survey_id)
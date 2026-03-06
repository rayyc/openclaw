# Step 11: WebSocket events � paste code here
# backend/api/routes/events.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.services.redis_service import subscribe_to_events
import asyncio, json

router = APIRouter(prefix="/ws", tags=["websockets"])

@router.websocket("/events/{user_id}")
async def websocket_events(websocket: WebSocket, user_id: str):
    await websocket.accept()
    try:
        async for event in subscribe_to_events(user_id):
            await websocket.send_text(json.dumps(event))
    except WebSocketDisconnect:
        pass
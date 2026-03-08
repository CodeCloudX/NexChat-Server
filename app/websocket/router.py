from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.infrastructure.database import async_session_maker
from app.repositories import user_repo
from app.websocket.manager import manager
from app.websocket import events
from app.core import security

websocket_router = APIRouter()

async def get_ws_user(session_id: str, device_id: str, ip_address: str):
    """
    Validates session for WebSocket connection using centralized security logic.
    """
    async with async_session_maker() as db:
        try:
            # Centralized Trust: Pass IP address for multi-layer validation
            session = await security.validate_session_request(db, session_id, device_id, ip_address)
            
            user = await user_repo.get_user_by_id(db, user_id=session.user_id)
            if not user or not user.is_active:
                return None
            return user
        except Exception:
            return None


@websocket_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str = Query(...),
    device_id: str = Query(...)
):
    # Extract IP address from WebSocket scope
    client_ip = websocket.client.host
    
    user = await get_ws_user(session_id, device_id, client_ip)
    if not user:
        await websocket.close(code=1008) # Policy Violation
        return

    await manager.connect(websocket, user.id)

    try:
        while True:
            data = await websocket.receive_json()
            await events.dispatch_event(user.id, data)
    except WebSocketDisconnect:
        await manager.disconnect(websocket, user.id)
    except Exception:
        await manager.disconnect(websocket, user.id)

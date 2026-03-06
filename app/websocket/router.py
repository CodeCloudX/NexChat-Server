from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError

from app.core import security
from app.core.config import settings
from app.websocket.manager import manager
from app.websocket import events
from app.infrastructure.database import async_session_maker
from app.repositories import user_repo

websocket_router = APIRouter()

async def get_ws_user(token: str):
    """
    Authenticated a WS user using the same logic as HTTP deps.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if not user_id:
            return None
            
        async with async_session_maker() as db:
            user = await user_repo.get_user_by_id(db, user_id=user_id)
            if not user or not user.is_active:
                return None
            return user
    except (JWTError, Exception):
        return None


@websocket_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    user = await get_ws_user(token)
    if not user:
        await websocket.close(code=1008) # Policy Violation
        return

    # ConnectionManager handles online status via presence_service
    await manager.connect(websocket, user.id)

    try:
        while True:
            data = await websocket.receive_json()
            await events.dispatch_event(user.id, data)
    except WebSocketDisconnect:
        await manager.disconnect(websocket, user.id)
    except Exception:
        await manager.disconnect(websocket, user.id)

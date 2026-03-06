from typing import Any, Dict
from sqlalchemy.sql import func
from app.websocket.manager import manager
from app.services import chat_service
from app.infrastructure.database import async_session_maker
from app.repositories import read_repo
from app.schemas.websocket import WSReadReceiptPayload
from app.utils import constants

async def handle_read_receipt(user_id: str, data: Dict[str, Any]):
    """
    Handles marking a message as DELIVERED or READ using Pydantic validation.
    """
    try:
        # Validate incoming data
        payload = WSReadReceiptPayload(
            message_id=data.get("message_id"),
            user_id=user_id,
            chat_id=data.get("chat_id"),
            status=data.get("status", "read"),
            timestamp=str(func.now())
        )
    except Exception:
        return # Ignore invalid events

    async with async_session_maker() as db:
        # 1. Fetch existing receipt
        db_obj = await read_repo.get_message_read_entry(db, message_id=payload.message_id, user_id=user_id)

        # 2. Update status in DB
        if payload.status == "delivered":
            if not db_obj:
                await read_repo.create_delivery_receipt(db, message_id=payload.message_id, user_id=user_id)
            else: return 
        
        elif payload.status == "read":
            await read_repo.mark_as_read(db, db_obj=db_obj, message_id=payload.message_id, user_id=user_id)

        # 3. Broadcast using standardized schema dump
        members = await chat_service.get_chat_members(db, chat_id=payload.chat_id)
        broadcast_data = {
            "type": constants.EVENT_STATUS_UPDATE,
            "payload": payload.model_dump()
        }
        await manager.broadcast(broadcast_data, members)

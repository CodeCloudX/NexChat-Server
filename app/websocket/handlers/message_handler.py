from typing import Any, Dict
from app.schemas.message import MessageCreate
from app.infrastructure.database import async_session_maker

async def handle_message(user_id: str, data: Dict[str, Any]):
    """
    Handles sending a new message via WebSocket.
    Now extremely thin as orchestration is handled by the service layer.
    """
    chat_id = data.get("chat_id")
    content = data.get("content")
    media_url = data.get("media_url")
    media_width = data.get("media_width")
    media_height = data.get("media_height")
    message_type = data.get("type", "text")

    if not chat_id:
        return

    # Modular Import to avoid Circular Dependency
    from app.services import message_service

    async with async_session_maker() as db:
        try:
            message_in = MessageCreate(
                chat_id=chat_id,
                content=content,
                media_url=media_url,
                media_width=media_width,
                media_height=media_height,
                type=message_type
            )
            
            # Service layer now handles: 
            # 1. Block checks
            # 2. DB persistence (if not blocked)
            # 3. Real-time WebSocket broadcast
            # 4. Background Push Notifications
            await message_service.send_message(db, message_in=message_in, sender_id=user_id)
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error in handle_message: {e}")

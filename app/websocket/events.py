import logging
from typing import Any, Dict
from app.websocket.handlers import message_handler, typing_handler, read_receipt_handler
from app.schemas.websocket import WSEventBase

logger = logging.getLogger(__name__)

async def dispatch_event(user_id: str, data: Dict[str, Any]):
    """
    Main dispatcher for incoming WebSocket events.
    Uses WSEventBase for initial validation.
    """
    try:
        # 1. Validate basic event structure
        event = WSEventBase(**data)
    except Exception as e:
        logger.warning(f"Invalid WebSocket event format from user {user_id}: {e}")
        return

    event_type = event.type
    payload = event.payload

    if event_type == "message":
        await message_handler.handle_message(user_id, payload)
    
    elif event_type == "typing":
        await typing_handler.handle_typing(user_id, payload)
        
    elif event_type == "read_receipt":
        await read_receipt_handler.handle_read_receipt(user_id, payload)
    
    else:
        logger.info(f"Unknown WebSocket event type: {event_type}")

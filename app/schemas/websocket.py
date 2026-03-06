from typing import Any, Dict, Optional, List
from pydantic import BaseModel
from app.schemas.message import MessageStatus

class WSEventBase(BaseModel):
    """Base structure for all WebSocket events."""
    type: str
    payload: Dict[str, Any]

class WSTypingPayload(BaseModel):
    chat_id: str
    user_id: str
    is_typing: bool

class WSMessagePayload(BaseModel):
    """Payload for real-time message broadcasts with CLS support."""
    id: str
    chat_id: str
    sender_id: str
    content: Optional[str] = None
    media_url: Optional[str] = None
    media_width: Optional[int] = None
    media_height: Optional[int] = None
    type: str
    created_at: str
    updated_at: Optional[str] = None
    status: List[MessageStatus] = []

class WSReadReceiptPayload(BaseModel):
    message_id: str
    user_id: str
    chat_id: str
    status: str # 'delivered' or 'read'
    timestamp: Optional[str] = None

class WSPresencePayload(BaseModel):
    user_id: str
    status: str # 'online' or 'offline'
    last_seen: Optional[str] = None

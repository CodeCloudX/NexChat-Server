from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.base import MessageType


class MessageBase(BaseModel):
    content: Optional[str] = None
    media_url: Optional[str] = None
    media_width: Optional[int] = None  # To prevent CLS
    media_height: Optional[int] = None # To prevent CLS
    type: MessageType = MessageType.TEXT


class MessageCreate(MessageBase):
    chat_id: str


class MessageUpdate(BaseModel):
    content: Optional[str] = None


class MessageStatus(BaseModel):
    user_id: str
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None


class MessageOut(MessageBase):
    id: str
    chat_id: str
    sender_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: List[MessageStatus] = []

    model_config = ConfigDict(from_attributes=True)

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.base import ChatType, MemberRole


class ChatMemberBase(BaseModel):
    user_id: str
    role: MemberRole = MemberRole.MEMBER

class UserSummary(BaseModel):
    id: str
    full_name: Optional[str]
    profile_photo_url: Optional[str]
    is_online: bool = False # Added for real-time status visibility

class MessageSummary(BaseModel):
    content: Optional[str]
    created_at: datetime
    sender_id: str

class ChatRoomBase(BaseModel):
    name: Optional[str] = None
    type: ChatType = ChatType.DIRECT

class ChatRoomCreate(ChatRoomBase):
    members: List[str]

class ChatRoomOut(ChatRoomBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # WhatsApp extras
    other_user: Optional[UserSummary] = None
    last_message: Optional[MessageSummary] = None

    model_config = ConfigDict(from_attributes=True)

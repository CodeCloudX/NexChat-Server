from sqlalchemy import Column, String, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from app.models.base import Base, MemberRole

class ChatMember(Base):
    __tablename__ = "chat_members"
    
    # Composite Primary Key already ensures uniqueness of (chat_id, user_id)
    chat_id = Column(String, ForeignKey("chat_rooms.id", ondelete="CASCADE"), primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    
    role = Column(Enum(MemberRole), default=MemberRole.MEMBER)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

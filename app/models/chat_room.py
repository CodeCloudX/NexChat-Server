from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.sql import func
from app.models.base import Base, ChatType

class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=True) # Only for groups
    type = Column(Enum(ChatType), default=ChatType.DIRECT)
    
    created_at = Column(DateTime(timezone=True), default=func.now(), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), server_default=func.now(), onupdate=func.now())

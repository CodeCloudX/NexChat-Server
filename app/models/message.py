from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Enum, Integer
from sqlalchemy.sql import func
from app.models.base import Base, MessageType

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, index=True)
    chat_id = Column(String, ForeignKey("chat_rooms.id"), index=True)
    sender_id = Column(String, ForeignKey("users.id"), index=True)
    content = Column(Text, nullable=True)
    media_url = Column(String, nullable=True)
    
    # New fields for frontend performance (CLS)
    media_width = Column(Integer, nullable=True)
    media_height = Column(Integer, nullable=True)
    
    type = Column(Enum(MessageType), default=MessageType.TEXT)
    created_at = Column(DateTime(timezone=True), default=func.now(), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), server_default=func.now(), onupdate=func.now())

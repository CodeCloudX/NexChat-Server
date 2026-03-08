from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

class MessageRead(Base):
    """
    Tracks both Delivery (Double Gray Tick) and Read (Blue Tick) status.
    """
    __tablename__ = "message_reads"
    
    # Composite Primary Key already ensures uniqueness of (message_id, user_id)
    message_id = Column(String, ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    # Jab message device tak pahunch gaya (Double Gray Tick)
    delivered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Jab user ne chat kholkar dekh li (Blue Tick)
    read_at = Column(DateTime(timezone=True), nullable=True)

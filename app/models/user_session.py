from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.models.base import Base

class UserSession(Base):
    """
    Combined Session and Device management (WhatsApp style).
    A user has one active session at a time, tied to a specific device and its push token.
    """
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, index=True) # session_id (uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Device details
    device_id = Column(String, nullable=False, index=True)
    device_name = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    
    # Push Notification Token (FCM) linked to this session
    fcm_token = Column(String, nullable=True, index=True)
    platform = Column(String, nullable=True) # android, ios, web
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Force single session per user by making user_id unique in this table
    __table_args__ = (UniqueConstraint('user_id', name='_user_single_session_uc'),)

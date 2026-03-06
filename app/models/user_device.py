from sqlalchemy import Column, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.models.base import Base

class UserDevice(Base):
    """
    Stores FCM tokens for users to enable push notifications.
    A user can have multiple devices (tokens).
    """
    __tablename__ = "user_devices"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    fcm_token = Column(String, nullable=False, index=True)
    platform = Column(String, default="android") # android, ios, web
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Ensure a user doesn't have duplicate entries for the same token
    __table_args__ = (UniqueConstraint('user_id', 'fcm_token', name='_user_fcm_token_uc'),)

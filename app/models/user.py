from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    profile_photo_url = Column(String, nullable=True)
    
    # WhatsApp style 'About' section
    bio = Column(String, default="Hey there! I am using NexChat.")

    is_active = Column(Boolean, default=True)
    is_profile_complete = Column(Boolean, default=False)
    
    # WhatsApp style Presence: Last seen stored in DB
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

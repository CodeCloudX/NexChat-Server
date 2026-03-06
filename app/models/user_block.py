from sqlalchemy import Column, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.models.base import Base

class UserBlock(Base):
    __tablename__ = "user_blocks"
    
    id = Column(String, primary_key=True, index=True)
    blocker_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    blocked_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # --- PERFORMANCE FIX: Prevents duplicate blocks at DB level ---
    __table_args__ = (
        UniqueConstraint('blocker_id', 'blocked_id', name='_blocker_blocked_uc'),
    )

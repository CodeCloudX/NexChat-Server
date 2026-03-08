from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import session_repo
from app.models.user_session import UserSession
from app.core.exceptions import UnauthorizedException
from app.utils import constants

logger = logging.getLogger(__name__)

async def start_session(
    db: AsyncSession, 
    *, 
    user_id: str, 
    device_id: str, 
    device_name: Optional[str], 
    ip_address: Optional[str],
    platform: Optional[str] = None
) -> UserSession:
    # 1. Single Device Logic: Delete old sessions for this user (WhatsApp style)
    await session_repo.delete_user_sessions(db, user_id=user_id)
    
    # 2. Create new session
    expires_at = datetime.now(timezone.utc) + timedelta(days=constants.SESSION_EXPIRE_DAYS)
    return await session_repo.create_session(
        db,
        user_id=user_id,
        device_id=device_id,
        device_name=device_name,
        ip_address=ip_address,
        expires_at=expires_at,
        platform=platform
    )

async def verify_session(db: AsyncSession, session_id: str, device_id: str, current_ip: str) -> UserSession:
    session = await session_repo.get_session(db, session_id)
    
    if not session:
        raise UnauthorizedException(detail="Session not found or expired")
        
    # Layer 1: Strict Device ID Check
    if session.device_id != device_id:
        await session_repo.delete_session(db, session_id)
        logger.warning(f"Security Alert: Device ID mismatch for session {session_id}. Expected {session.device_id}, got {device_id}")
        raise UnauthorizedException(detail="Security Alert: Device mismatch.")
        
    # Layer 2: IP Monitoring (Soft Check)
    if session.ip_address != current_ip:
        session.ip_address = current_ip
        
    # Layer 3: Expiry Check
    expires_at_utc = session.expires_at.replace(tzinfo=timezone.utc)
    if expires_at_utc < datetime.now(timezone.utc):
        await session_repo.delete_session(db, session_id)
        raise UnauthorizedException(detail="Session expired")
        
    # Refresh session activity and expiry
    new_expiry = datetime.now(timezone.utc) + timedelta(days=constants.SESSION_EXPIRE_DAYS)
    await session_repo.update_session_activity(db, session, new_expiry)
    
    return session

async def end_session(db: AsyncSession, session_id: str):
    await session_repo.delete_session(db, session_id)

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from app.models.user_session import UserSession
from app.core import security

async def create_session(
    db: AsyncSession, 
    *, 
    user_id: str, 
    device_id: str, 
    device_name: Optional[str], 
    ip_address: Optional[str],
    expires_at: any,
    platform: Optional[str] = None
) -> UserSession:
    """
    Creates a new session using high-entropy ID from security.py.
    """
    db_obj = UserSession(
        id=security.generate_session_id(),
        user_id=user_id,
        device_id=device_id,
        device_name=device_name,
        ip_address=ip_address,
        expires_at=expires_at,
        platform=platform
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_session(db: AsyncSession, session_id: str) -> Optional[UserSession]:
    return await db.get(UserSession, session_id)

async def delete_user_sessions(db: AsyncSession, user_id: str):
    """Deletes all sessions for a user (Single device login logic)."""
    stmt = delete(UserSession).where(UserSession.user_id == user_id)
    await db.execute(stmt)
    await db.commit()

async def delete_session(db: AsyncSession, session_id: str):
    stmt = delete(UserSession).where(UserSession.id == session_id)
    await db.execute(stmt)
    await db.commit()

async def update_session_activity(db: AsyncSession, session: UserSession, new_expiry: any):
    session.expires_at = new_expiry
    db.add(session)
    await db.commit()
    await db.refresh(session)

async def update_session_fcm_token(db: AsyncSession, session: UserSession, token: str, platform: str):
    session.fcm_token = token
    session.platform = platform
    db.add(session)
    await db.commit()
    await db.refresh(session)

async def get_all_user_fcm_tokens(db: AsyncSession, user_id: str) -> List[str]:
    """Fetches all FCM tokens linked to active sessions for a user."""
    result = await db.execute(
        select(UserSession.fcm_token).where(
            UserSession.user_id == user_id,
            UserSession.fcm_token.isnot(None)
        )
    )
    return result.scalars().all()

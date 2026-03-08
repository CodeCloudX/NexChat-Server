import secrets
import hashlib
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_session import UserSession

def generate_session_id() -> str:
    """
    Generates a cryptographically strong session identifier.
    Uses secrets module for production-grade randomness.
    """
    return secrets.token_urlsafe(32)

def hash_session_id(session_id: str) -> str:
    """
    Optional: Hashes the session ID for storage if you want 
    extra protection against DB leaks.
    """
    return hashlib.sha256(session_id.encode()).hexdigest()

async def validate_session_request(
    db: AsyncSession, 
    session_id: str, 
    device_id: str,
    ip_address: str
) -> UserSession:
    """
    Core security function to trust and validate a session.
    Multi-layer validation: Session ID, Device ID, and IP monitoring.
    """
    # Import inside function to avoid circular dependency with session_repo/service
    from app.services import session_service
    return await session_service.verify_session(db, session_id, device_id, ip_address)

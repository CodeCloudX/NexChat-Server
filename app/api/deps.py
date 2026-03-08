from typing import Generator, Optional
from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    UnauthorizedException, 
    UserNotFoundException,
    InactiveUserException
)
from app.models.user import User
from app.repositories import user_repo
from app.infrastructure.database import async_session_maker
from app.core import security

async def get_db() -> Generator:
    async with async_session_maker() as session:
        yield session

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None),
    device_id: Optional[str] = Header(None, alias="Device-Id")
) -> User:
    """
    Dependency that validates Session ID and returns the current user.
    Uses multi-layer security: Session ID, Device ID, and IP address.
    """
    if not authorization or not authorization.startswith("Session "):
        raise UnauthorizedException(detail="Not authenticated. Session required.")
    
    if not device_id:
        raise UnauthorizedException(detail="Device-Id header required.")

    session_id = authorization.replace("Session ", "")
    client_ip = request.client.host
    
    # CORE SECURITY VALIDATION (Multi-layer)
    user_session = await security.validate_session_request(db, session_id, device_id, client_ip)
    
    user = await user_repo.get_user_by_id(db, user_id=user_session.user_id)
    if not user:
        raise UserNotFoundException()
    
    if not user.is_active:
        raise InactiveUserException()

    return user

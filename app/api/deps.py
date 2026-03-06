from typing import Generator
from fastapi import Depends
from fastapi.security import APIKeyHeader
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core import security
from app.core.exceptions import (
    UnauthorizedException, 
    ForbiddenException, 
    UserNotFoundException,
    InactiveUserException
)
from app.models.user import User
from app.repositories import user_repo
from app.infrastructure.database import async_session_maker

# Standard Bearer token header instead of OAuth2PasswordBearer
reusable_oauth2 = APIKeyHeader(name="Authorization", auto_error=False)

async def get_db() -> Generator:
    """
    Dependency that provides an async database session per request.
    """
    async with async_session_maker() as session:
        yield session

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    """
    Dependency that validates JWT and returns the current user.
    Standardized to use custom exceptions.
    """
    if not token:
        raise UnauthorizedException(detail="Not authenticated")
    
    # Handle 'Bearer <token>' format
    if token.startswith("Bearer "):
        token = token.split(" ")[1]

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException(detail="Invalid token payload")
    except JWTError:
        raise UnauthorizedException(detail="Could not validate credentials")
    
    user = await user_repo.get_user_by_id(db, user_id=user_id)
    if not user:
        raise UserNotFoundException()
    
    if not user.is_active:
        raise InactiveUserException()

    return user

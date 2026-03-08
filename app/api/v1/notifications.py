from typing import Any
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.schemas.notification import NotificationTokenCreate, NotificationResponse
from app.services import notification_service

router = APIRouter()


@router.post("/tokens", response_model=NotificationResponse)
async def register_device_token(
    *,
    db: AsyncSession = Depends(deps.get_db),
    token_in: NotificationTokenCreate,
    current_user: User = Depends(deps.get_current_user),
    request: Request
) -> Any:
    """
    Links an FCM token to the current active session.
    """
    # Extract session_id from header
    auth_header = request.headers.get("Authorization")
    session_id = auth_header.replace("Session ", "") if auth_header else None
    
    await notification_service.register_device(
        db, user_id=current_user.id, session_id=session_id, device_in=token_in
    )
    return {"status": "ok", "message": "Device token linked to session successfully"}

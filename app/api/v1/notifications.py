from typing import Any
from fastapi import APIRouter, Depends, Query
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
) -> Any:
    """
    Register a new FCM device token for the current user.
    """
    await notification_service.register_device(
        db, user_id=current_user.id, device_in=token_in
    )
    return {"status": "ok", "message": "Device token registered successfully"}


@router.delete("/tokens", response_model=NotificationResponse)
async def unregister_device_token(
    *,
    db: AsyncSession = Depends(deps.get_db),
    token: str = Query(..., description="The FCM token to remove"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Remove a specific device token (e.g., during logout).
    """
    await notification_service.unregister_device(
        db, user_id=current_user.id, token=token
    )
    return {"status": "ok", "message": "Device token removed successfully"}

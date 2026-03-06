from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import notification_repo
from app.schemas.notification import NotificationTokenCreate, NotificationPayload
from app.background.tasks import send_notification_task

async def register_device(db: AsyncSession, *, user_id: str, device_in: NotificationTokenCreate):
    """
    Registers or updates a user's device FCM token.
    """
    existing_device = await notification_repo.get_device_token(
        db, user_id=user_id, token=device_in.token
    )
    
    if existing_device:
        await notification_repo.update_device_last_active(db, db_obj=existing_device)
    else:
        await notification_repo.create_device_token(
            db, 
            user_id=user_id, 
            token=device_in.token, 
            platform=device_in.platform
        )

async def unregister_device(db: AsyncSession, *, user_id: str, token: str):
    """Removes a device token from the database."""
    device = await notification_repo.get_device_token(db, user_id=user_id, token=token)
    if device:
        await notification_repo.delete_device_token(db, db_obj=device)

async def notify_user(db: AsyncSession, *, user_id: str, payload: NotificationPayload):
    """
    Fetches all device tokens for a user and triggers a background notification task.
    Uses NotificationPayload for structured data.
    """
    tokens = await notification_repo.get_all_user_tokens(db, user_id=user_id)
    if tokens:
        # payload.model_dump() ensures we send a clean dictionary to the background task
        await send_notification_task(
            tokens=tokens,
            title=payload.title,
            body=payload.body,
            data=payload.data
        )

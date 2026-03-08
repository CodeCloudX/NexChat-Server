from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import session_repo
from app.schemas.notification import NotificationTokenCreate, NotificationPayload
from app.background.tasks import send_notification_task

async def register_device(db: AsyncSession, *, user_id: str, session_id: str, device_in: NotificationTokenCreate):
    """
    Links an FCM token to a specific user session.
    """
    session = await session_repo.get_session(db, session_id)
    if session and session.user_id == user_id:
        await session_repo.update_session_fcm_token(
            db, 
            session=session, 
            token=device_in.token, 
            platform=device_in.platform
        )

async def unregister_device(db: AsyncSession, *, user_id: str, session_id: str):
    """Removes the FCM token from a specific session."""
    session = await session_repo.get_session(db, session_id)
    if session and session.user_id == user_id:
        await session_repo.update_session_fcm_token(db, session=session, token=None, platform="android")

async def notify_user(db: AsyncSession, *, user_id: str, payload: NotificationPayload):
    """
    Fetches all FCM tokens linked to active sessions for a user.
    """
    tokens = await session_repo.get_all_user_fcm_tokens(db, user_id=user_id)
    if tokens:
        await send_notification_task(
            tokens=tokens,
            title=payload.title,
            body=payload.body,
            data=payload.data
        )

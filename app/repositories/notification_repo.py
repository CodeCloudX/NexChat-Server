from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.user_device import UserDevice
from app.utils import helpers

async def get_device_token(db: AsyncSession, *, user_id: str, token: str) -> Optional[UserDevice]:
    """Fetch a specific device token record."""
    result = await db.execute(
        select(UserDevice).where(
            UserDevice.user_id == user_id, 
            UserDevice.fcm_token == token
        )
    )
    return result.scalars().first()

async def create_device_token(db: AsyncSession, *, user_id: str, token: str, platform: str) -> UserDevice:
    """Creates a new device token record."""
    db_obj = UserDevice(
        id=helpers.generate_uuid(),
        user_id=user_id,
        fcm_token=token,
        platform=platform
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def update_device_last_active(db: AsyncSession, *, db_obj: UserDevice):
    """Updates the last_active timestamp for a device."""
    db_obj.last_active = func.now()
    await db.commit()
    await db.refresh(db_obj)

async def get_all_user_tokens(db: AsyncSession, user_id: str) -> List[str]:
    """Returns a list of all raw FCM tokens for a user."""
    result = await db.execute(
        select(UserDevice.fcm_token).where(UserDevice.user_id == user_id)
    )
    return result.scalars().all()

async def delete_device_token(db: AsyncSession, *, db_obj: UserDevice):
    """Deletes a device token record."""
    await db.delete(db_obj)
    await db.commit()

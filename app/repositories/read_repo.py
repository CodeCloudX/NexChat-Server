from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.message_read import MessageRead

async def get_message_read_entry(db: AsyncSession, *, message_id: str, user_id: str) -> Optional[MessageRead]:
    """Fetch a specific read/delivery receipt."""
    result = await db.execute(
        select(MessageRead).where(
            MessageRead.message_id == message_id,
            MessageRead.user_id == user_id
        )
    )
    return result.scalars().first()

async def create_delivery_receipt(db: AsyncSession, *, message_id: str, user_id: str) -> MessageRead:
    """Creates a 'Delivered' (Gray Tick) status."""
    db_obj = MessageRead(message_id=message_id, user_id=user_id)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def mark_as_read(db: AsyncSession, *, db_obj: Optional[MessageRead], message_id: str = None, user_id: str = None):
    """Updates status to 'Read' (Blue Tick)."""
    if db_obj:
        if not db_obj.read_at:
            db_obj.read_at = func.now()
            await db.commit()
            await db.refresh(db_obj)
    elif message_id and user_id:
        # If no delivery receipt exists yet, create directly as read
        db_obj = MessageRead(message_id=message_id, user_id=user_id, read_at=func.now())
        db.add(db_obj)
        await db.commit()

async def get_all_statuses_for_message(db: AsyncSession, message_id: str) -> List[MessageRead]:
    """Fetch all recipients' status for a specific message."""
    result = await db.execute(
        select(MessageRead).where(MessageRead.message_id == message_id)
    )
    return result.scalars().all()

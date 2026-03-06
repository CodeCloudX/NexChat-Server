from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.message import Message, MessageType
from app.utils import helpers


async def create_message(
    db: AsyncSession, 
    chat_id: str, 
    sender_id: str, 
    content: Optional[str] = None, 
    media_url: Optional[str] = None, 
    media_width: Optional[int] = None,
    media_height: Optional[int] = None,
    type: MessageType = MessageType.TEXT
) -> Message:
    """Creates a new message with optional media dimensions."""
    db_obj = Message(
        id=helpers.generate_uuid(),
        chat_id=chat_id,
        sender_id=sender_id,
        content=content,
        media_url=media_url,
        media_width=media_width,
        media_height=media_height,
        type=type
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_chat_messages(db: AsyncSession, chat_id: str, limit: int = 50, skip: int = 0) -> List[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_message_by_id(db: AsyncSession, message_id: str) -> Optional[Message]:
    return await db.get(Message, message_id)


async def delete_message(db: AsyncSession, message_id: str):
    db_obj = await db.get(Message, message_id)
    if db_obj:
        await db.delete(db_obj)
        await db.commit()

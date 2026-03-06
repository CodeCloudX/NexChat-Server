from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from app.models.chat_room import ChatRoom, ChatType
from app.models.chat_member import ChatMember, MemberRole
from app.models.user_block import UserBlock
from app.utils import helpers


async def get_chat_by_id(db: AsyncSession, chat_id: str) -> Optional[ChatRoom]:
    return await db.get(ChatRoom, chat_id)


async def get_user_chats(db: AsyncSession, user_id: str) -> List[ChatRoom]:
    result = await db.execute(
        select(ChatRoom)
        .join(ChatMember)
        .where(ChatMember.user_id == user_id)
        .order_by(ChatRoom.updated_at.desc())
    )
    return result.scalars().all()


async def get_chat_members(db: AsyncSession, chat_id: str) -> List[str]:
    result = await db.execute(
        select(ChatMember.user_id).where(ChatMember.chat_id == chat_id)
    )
    return result.scalars().all()


async def create_chat_room(db: AsyncSession, name: str = None, type: ChatType = ChatType.DIRECT) -> ChatRoom:
    db_obj = ChatRoom(id=helpers.generate_uuid(), name=name, type=type)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def add_member_to_chat(db: AsyncSession, chat_id: str, user_id: str, role: MemberRole = MemberRole.MEMBER):
    db_obj = ChatMember(chat_id=chat_id, user_id=user_id, role=role)
    db.add(db_obj)
    await db.commit()


async def get_direct_chat_between_users(db: AsyncSession, user1_id: str, user2_id: str) -> Optional[ChatRoom]:
    if user1_id == user2_id:
        stmt = (
            select(ChatMember.chat_id)
            .group_by(ChatMember.chat_id)
            .having(func.count(ChatMember.user_id) == 1)
            .where(ChatMember.user_id == user1_id)
        )
        result = await db.execute(stmt)
        chat_id = result.scalar()
        if chat_id:
            return await db.get(ChatRoom, chat_id)
        return None

    two_member_chats_query = (
        select(ChatMember.chat_id)
        .group_by(ChatMember.chat_id)
        .having(func.count(ChatMember.user_id) == 2)
    )

    stmt = (
        select(ChatMember.chat_id)
        .where(ChatMember.chat_id.in_(two_member_chats_query))
        .where(ChatMember.user_id.in_([user1_id, user2_id]))
        .group_by(ChatMember.chat_id)
        .having(func.count(ChatMember.user_id) == 2)
    )

    result = await db.execute(stmt)
    chat_id = result.scalar()

    if chat_id:
        return await db.get(ChatRoom, chat_id)
    return None

async def get_all_chat_partners(db: AsyncSession, user_id: str) -> List[str]:
    """
    Finds all users sharing a room with user_id, 
    EXCLUDING those where a block exists (bidirectional).
    """
    # 1. Get all room IDs the user is in
    user_rooms_stmt = select(ChatMember.chat_id).where(ChatMember.user_id == user_id)
    user_rooms = (await db.execute(user_rooms_stmt)).scalars().all()
    
    if not user_rooms:
        return []

    # 2. Get all other members in those rooms
    partners_stmt = select(ChatMember.user_id).where(
        ChatMember.chat_id.in_(user_rooms),
        ChatMember.user_id != user_id
    ).distinct()
    partners = (await db.execute(partners_stmt)).scalars().all()
    
    if not partners:
        return []

    # 3. Filter out blocks (bidirectional)
    # Get IDs of people I blocked OR who blocked me
    block_stmt = select(UserBlock).where(
        or_(
            (UserBlock.blocker_id == user_id) & (UserBlock.blocked_id.in_(partners)),
            (UserBlock.blocker_id.in_(partners)) & (UserBlock.blocked_id == user_id)
        )
    )
    blocks = (await db.execute(block_stmt)).scalars().all()
    
    blocked_ids = set()
    for b in blocks:
        blocked_ids.add(b.blocked_id if b.blocker_id == user_id else b.blocker_id)

    return [p for p in partners if p not in blocked_ids]

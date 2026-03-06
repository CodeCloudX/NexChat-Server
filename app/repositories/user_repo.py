from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from app.models.user import User
from app.models.user_block import UserBlock
from app.utils import helpers


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Retrieve a user by their exact email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def search_users_by_query(db: AsyncSession, query: str, limit: int = 10) -> List[User]:
    """
    Suggestive search: Matches ONLY partial email.
    Server-side validation in service layer ensures query contains '@'.
    """
    search_pattern = f"%{query}%"
    result = await db.execute(
        select(User)
        .where(User.email.ilike(search_pattern))
        .limit(limit)
    )
    return result.scalars().all()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """Retrieve a user by their UUID."""
    return await db.get(User, user_id)


async def is_user_blocked(db: AsyncSession, blocker_id: str, blocked_id: str) -> bool:
    """Efficiently check for block existence using ID only."""
    result = await db.execute(
        select(UserBlock.id).where(
            UserBlock.blocker_id == blocker_id,
            UserBlock.blocked_id == blocked_id
        ).limit(1)
    )
    return result.scalar() is not None


async def block_user(db: AsyncSession, blocker_id: str, blocked_id: str) -> bool:
    """Atomic block creation using DB unique constraints."""
    try:
        db_obj = UserBlock(id=helpers.generate_uuid(), blocker_id=blocker_id, blocked_id=blocked_id)
        db.add(db_obj)
        await db.commit()
        return True
    except Exception:
        await db.rollback()
        return False


async def unblock_user(db: AsyncSession, blocker_id: str, blocked_id: str) -> bool:
    """Atomic removal of a block record."""
    stmt = delete(UserBlock).where(
        UserBlock.blocker_id == blocker_id,
        UserBlock.blocked_id == blocked_id
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def get_blocked_users(db: AsyncSession, blocker_id: str) -> List[User]:
    """Fetch users blocked by the requester with a join for profile data."""
    result = await db.execute(
        select(User)
        .join(UserBlock, User.id == UserBlock.blocked_id)
        .where(UserBlock.blocker_id == blocker_id)
    )
    return result.scalars().all()

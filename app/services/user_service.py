from typing import Any, Dict, List, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.core.exceptions import UserNotFoundException, NexChatException
from app.repositories import user_repo
from app.models.user import User
from app.schemas.user import UserUpdate
from app.utils import helpers


async def get_user_by_id(db: AsyncSession, user_id: str) -> User:
    """Internal helper to get user or raise exception."""
    user = await user_repo.get_user_by_id(db, user_id=user_id)
    if not user:
        raise UserNotFoundException()
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Helper to get user by email for registration and auth checks."""
    return await user_repo.get_user_by_email(db, email=email)


async def get_user_profile(db: AsyncSession, *, target_user_id: str, current_user_id: str, user_obj: Optional[User] = None) -> User:
    """
    Fetches a user profile with privacy checks and real-time status.
    """
    from app.services import presence_service
    
    if target_user_id != current_user_id:
        if await user_repo.is_user_blocked(db, blocker_id=target_user_id, blocked_id=current_user_id):
            raise UserNotFoundException()

    user = user_obj if user_obj else await get_user_by_id(db, user_id=target_user_id)
    is_blocked_by_me = await user_repo.is_user_blocked(db, blocker_id=current_user_id, blocked_id=user.id)
    
    if is_blocked_by_me and target_user_id != current_user_id:
        user.is_online = False
    else:
        user.is_online = await presence_service.get_user_status(user.id) == "online"
        
    return user


async def find_contacts_by_query(db: AsyncSession, *, query: str, current_user_id: str) -> List[User]:
    if '@' not in query:
        return []

    from app.services import presence_service
    users = await user_repo.search_users_by_query(db, query=query)
    results = []
    
    for user in users:
        is_blocked_by_them = await user_repo.is_user_blocked(db, blocker_id=user.id, blocked_id=current_user_id)
        if user.id != current_user_id and is_blocked_by_them:
            continue
            
        is_blocked_by_me = await user_repo.is_user_blocked(db, blocker_id=current_user_id, blocked_id=user.id)
        
        if is_blocked_by_me and user.id != current_user_id:
            user.is_online = False
        else:
            user.is_online = await presence_service.get_user_status(user.id) == "online"
            
        if user.id == current_user_id and user.full_name and not user.full_name.endswith(" (You)"):
            user.full_name = f"{user.full_name} (You)"
            
        results.append(user)
    return results


async def create_passwordless_user(db: AsyncSession, *, email: str, full_name: Optional[str] = None) -> User:
    """Creates a new user. Always sets is_profile_complete to False."""
    db_obj = User(
        id=helpers.generate_uuid(),
        email=email,
        full_name=full_name or email.split('@')[0],
        is_profile_complete=False
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_user(
    db: AsyncSession, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]], mark_complete: bool = False
) -> User:
    """
    Updates user data. 
    If mark_complete is True, the profile is marked as setup.
    """
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)
    
    for field in update_data:
        if hasattr(db_obj, field):
            setattr(db_obj, field, update_data[field])
    
    if mark_complete:
        db_obj.is_profile_complete = True
            
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_profile_photo(db: AsyncSession, *, user: User, file: UploadFile) -> Optional[str]:
    from app.services import media_service  
    url = await media_service.upload_profile_photo(user_id=user.id, file=file)
    if url:
        # Photo update via API usually happens during setup, but we don't automatically mark complete here
        # so the 'Save' button logic remains consistent.
        await update_user(db, db_obj=user, obj_in={"profile_photo_url": url}, mark_complete=False)
    return url


async def block_user(db: AsyncSession, *, blocker_id: str, blocked_id: str) -> bool:
    if blocker_id == blocked_id:
        raise NexChatException(status_code=400, detail="You cannot block yourself")
    target_user = await user_repo.get_user_by_id(db, user_id=blocked_id)
    if not target_user:
        raise UserNotFoundException()
    was_blocked = await user_repo.block_user(db, blocker_id, blocked_id)
    if was_blocked:
        from app.websocket.manager import manager
        from app.utils import constants
        await manager.broadcast({"type": constants.EVENT_PRESENCE, "payload": {"user_id": blocker_id, "status": "offline"}}, [blocked_id])
        await manager.broadcast({"type": constants.EVENT_PRESENCE, "payload": {"user_id": blocked_id, "status": "offline"}}, [blocker_id])
    return was_blocked


async def unblock_user(db: AsyncSession, *, blocker_id: str, blocked_id: str) -> bool:
    if blocker_id == blocked_id:
        raise NexChatException(status_code=400, detail="You cannot unblock yourself")
    target_user = await user_repo.get_user_by_id(db, user_id=blocked_id)
    if not target_user:
        raise UserNotFoundException()
    was_unblocked = await user_repo.unblock_user(db, blocker_id, blocked_id)
    if was_unblocked:
        from app.services import presence_service
        from app.websocket.manager import manager
        from app.utils import constants
        blocker_status = await presence_service.get_user_status(blocker_id)
        await manager.broadcast({"type": constants.EVENT_PRESENCE, "payload": {"user_id": blocker_id, "status": blocker_status}}, [blocked_id])
        blocked_status = await presence_service.get_user_status(blocked_id)
        await manager.broadcast({"type": constants.EVENT_PRESENCE, "payload": {"user_id": blocked_id, "status": blocked_status}}, [blocker_id])
    return was_unblocked


async def get_my_blocked_users(db: AsyncSession, *, user_id: str) -> List[User]:
    return await user_repo.get_blocked_users(db, blocker_id=user_id)

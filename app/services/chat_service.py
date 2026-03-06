import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.chat_room import ChatRoom
from app.models.base import ChatType, MemberRole
from app.models.message import Message
from app.models.user import User
from app.repositories import chat_repo, user_repo
from app.schemas.chat import ChatRoomCreate
from app.core.exceptions import ChatNotFoundException, UserNotFoundException
from app.infrastructure.redis import redis_client
from app.utils import constants

# Using centralized constant for Redis key
CHAT_MEMBERS_KEY = "chat_members:{chat_id}"

async def _enrich_chat_room(db: AsyncSession, room: ChatRoom, current_user_id: str) -> dict:
    """Helper function to add 'other_user' and 'last_message' with real-time status and privacy."""
    from app.services import presence_service # Inline import to avoid circular dep

    room_dict = {
        "id": room.id, "name": room.name, "type": room.type,
        "created_at": room.created_at, "updated_at": room.updated_at,
        "other_user": None, "last_message": None
    }
    
    # Get Last Message
    last_msg_query = (select(Message).where(Message.chat_id == room.id).order_by(Message.created_at.desc()).limit(1))
    last_msg_result = await db.execute(last_msg_query)
    last_msg = last_msg_result.scalars().first()
    if last_msg:
        room_dict["last_message"] = {"content": last_msg.content, "created_at": last_msg.created_at, "sender_id": last_msg.sender_id}
    
    # Get Other User for Direct Chats
    if room.type == ChatType.DIRECT:
        members = await get_chat_members(db, chat_id=room.id)
        other_user_id = next((m for m in members if m != current_user_id), None)
        if other_user_id:
            other_user = await user_repo.get_user_by_id(db, other_user_id)
            if other_user:
                # --- PRIVACY FIX: Check for block before fetching status ---
                is_blocked = await user_repo.is_user_blocked(db, blocker_id=current_user_id, blocked_id=other_user.id) or \
                             await user_repo.is_user_blocked(db, blocker_id=other_user.id, blocked_id=current_user_id)
                
                is_online = False
                if not is_blocked:
                    is_online = await presence_service.get_user_status(other_user.id) == "online"

                room_dict["other_user"] = {
                    "id": other_user.id, 
                    "full_name": other_user.full_name, 
                    "profile_photo_url": other_user.profile_photo_url,
                    "is_online": is_online
                }
    return room_dict

async def get_user_chats(db: AsyncSession, *, user_id: str, limit: int = constants.DEFAULT_PAGE_LIMIT, skip: int = 0) -> List[dict]:
    rooms = await chat_repo.get_user_chats(db, user_id=user_id)
    paginated_rooms = rooms[skip : skip + limit]
    return [await _enrich_chat_room(db, room, user_id) for room in paginated_rooms]

async def create_chat_room(db: AsyncSession, *, chat_in: ChatRoomCreate, creator_id: str) -> dict:
    for member_id in chat_in.members:
        if not await user_repo.get_user_by_id(db, member_id): raise UserNotFoundException()
    
    target_room = None
    if chat_in.type == ChatType.DIRECT and len(chat_in.members) == 1:
        target_room = await chat_repo.get_direct_chat_between_users(db, creator_id, chat_in.members[0])
    
    if not target_room:
        target_room = await chat_repo.create_chat_room(db, name=chat_in.name, type=chat_in.type)
        await chat_repo.add_member_to_chat(db, chat_id=target_room.id, user_id=creator_id, role=MemberRole.ADMIN)
        for m_id in chat_in.members:
            if m_id != creator_id: await chat_repo.add_member_to_chat(db, chat_id=target_room.id, user_id=m_id)
    
    await db.refresh(target_room)
    await redis_client.delete(CHAT_MEMBERS_KEY.format(chat_id=target_room.id))
    return await _enrich_chat_room(db, target_room, creator_id)

async def get_chat(db: AsyncSession, *, chat_id: str) -> Optional[ChatRoom]:
    return await chat_repo.get_chat_by_id(db, chat_id=chat_id)

async def get_enriched_chat(db: AsyncSession, *, chat_id: str, current_user_id: str) -> dict:
    chat = await get_chat(db, chat_id=chat_id)
    if not chat: raise ChatNotFoundException()
    return await _enrich_chat_room(db, chat, current_user_id)

async def get_chat_members(db: AsyncSession, *, chat_id: str) -> List[str]:
    cache_key = CHAT_MEMBERS_KEY.format(chat_id=chat_id)
    cached_members = await redis_client.get(cache_key)
    if cached_members: return json.loads(cached_members)
    members = await chat_repo.get_chat_members(db, chat_id=chat_id)
    await redis_client.set(cache_key, json.dumps(members), expire=constants.CHAT_MEMBERS_CACHE_TTL)
    return members

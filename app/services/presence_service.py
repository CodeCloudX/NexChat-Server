import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from app.infrastructure.redis import redis_client
from app.schemas.websocket import WSPresencePayload
from app.utils import constants, helpers
from app.repositories import chat_repo

logger = logging.getLogger(__name__)

USER_ONLINE_KEY = "online:{user_id}"

async def set_user_online(user_id: str):
    """
    Marks user as online and broadcasts to all their chat partners.
    """
    from app.websocket.manager import manager # Late import to avoid circular dependency
    from app.infrastructure.database import async_session_maker

    try:
        await redis_client.set(
            USER_ONLINE_KEY.format(user_id=user_id), 
            "1", 
            expire=constants.PRESENCE_TTL
        )
        
        payload = WSPresencePayload(user_id=user_id, status="online")
        message_data = {"type": constants.EVENT_PRESENCE, "payload": payload.model_dump()}
        
        async with async_session_maker() as db:
            partners = await chat_repo.get_all_chat_partners(db, user_id=user_id)
            if partners:
                await manager.broadcast(message_data, partners)
                
    except Exception as e:
        logger.error(f"Error setting user online: {e}")

async def set_user_offline(db: AsyncSession, user_id: str):
    """
    Marks user as offline, updates DB last_seen, and broadcasts to partners.
    """
    from app.websocket.manager import manager # Late import to avoid circular dependency

    try:
        await redis_client.delete(USER_ONLINE_KEY.format(user_id=user_id))
        
        from app.models.user import User
        user = await db.get(User, user_id)
        last_seen_iso = None
        if user:
            user.last_seen = func.now()
            await db.commit()
            await db.refresh(user)
            last_seen_iso = helpers.format_timestamp(user.last_seen)
            
        payload = WSPresencePayload(
            user_id=user_id, 
            status="offline", 
            last_seen=last_seen_iso
        )
        message_data = {"type": constants.EVENT_PRESENCE, "payload": payload.model_dump()}
        
        partners = await chat_repo.get_all_chat_partners(db, user_id=user_id)
        if partners:
            await manager.broadcast(message_data, partners)
            
    except Exception as e:
        logger.error(f"Error setting user offline: {e}")

async def get_user_status(user_id: str) -> str:
    """Checks Redis for user online status."""
    is_online = await redis_client.get(USER_ONLINE_KEY.format(user_id=user_id))
    return "online" if is_online else "offline"

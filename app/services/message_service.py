from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import Message
from app.models.chat_room import ChatRoom
from app.repositories import message_repo, user_repo, chat_repo, read_repo
from app.schemas.message import MessageCreate, MessageUpdate
from app.schemas.websocket import WSMessagePayload
from app.schemas.notification import NotificationPayload
from sqlalchemy.sql import func
from app.websocket.manager import manager
from app.core.exceptions import ChatNotFoundException, ForbiddenException, NexChatException
from app.utils import constants, helpers


async def send_message(db: AsyncSession, *, message_in: MessageCreate, sender_id: str) -> Message:
    """
    Strict Production Logic: Requires a valid chat_id.
    """
    chat_id = message_in.chat_id
    
    # 1. Validate Room Existence
    from app.services import chat_service
    room = await chat_service.get_chat(db, chat_id=chat_id)
    if not room:
        raise ChatNotFoundException()

    # 2. Block Check (Bidirectional Ghost Block)
    is_blocked = False
    members = await chat_service.get_chat_members(db, chat_id=chat_id)
    receiver_id = next((m for m in members if m != sender_id), None)
    
    if receiver_id:
        if await user_repo.is_user_blocked(db, blocker_id=sender_id, blocked_id=receiver_id) or \
           await user_repo.is_user_blocked(db, blocker_id=receiver_id, blocked_id=sender_id):
            is_blocked = True

    # 3. IF BLOCKED: Silent success (Sender only)
    if is_blocked:
        fake_id = helpers.generate_uuid()
        payload = WSMessagePayload(
            id=fake_id, chat_id=chat_id, sender_id=sender_id,
            content=message_in.content, media_url=message_in.media_url,
            type=message_in.type.value, created_at=helpers.format_timestamp(helpers.get_now()),
            status=[]
        )
        await manager.broadcast({"type": constants.EVENT_MESSAGE, "payload": payload.model_dump()}, [sender_id])
        return Message(id=fake_id, chat_id=chat_id, sender_id=sender_id, content=message_in.content, type=message_in.type)

    # 4. IF NOT BLOCKED: Save & Broadcast
    message = await message_repo.create_message(
        db, chat_id=chat_id, sender_id=sender_id,
        content=message_in.content, media_url=message_in.media_url, 
        media_width=message_in.media_width, media_height=message_in.media_height,
        type=message_in.type
    )
    
    room.updated_at = func.now()
    await db.commit()
    await db.refresh(message)
    
    payload = WSMessagePayload(
        id=message.id, chat_id=chat_id, sender_id=message.sender_id,
        content=message.content, media_url=message.media_url,
        media_width=message.media_width, media_height=message.media_height,
        type=message.type.value, created_at=helpers.format_timestamp(message.created_at),
        updated_at=helpers.format_timestamp(message.updated_at),
        status=[]
    )
    
    await manager.broadcast({"type": constants.EVENT_MESSAGE, "payload": payload.model_dump()}, members)

    # 5. Background Push Notifications
    from app.services import notification_service
    notif_payload = NotificationPayload(
        title="New Message",
        body=message.content or "Sent an attachment",
        data={"chat_id": chat_id, "type": "new_message"}
    )
    for m_id in members:
        if m_id != sender_id:
            await notification_service.notify_user(db, user_id=m_id, payload=notif_payload)

    return message

async def get_chat_messages(db: AsyncSession, *, chat_id: str, limit: int = constants.DEFAULT_PAGE_LIMIT, skip: int = 0) -> List[dict]:
    """Retrieves messages for a chat room."""
    messages = await message_repo.get_chat_messages(db, chat_id=chat_id, limit=limit, skip=skip)
    enriched_messages = []
    for msg in messages:
        statuses = await read_repo.get_all_statuses_for_message(db, message_id=msg.id)
        enriched_messages.append({
            "id": msg.id, "chat_id": msg.chat_id, "sender_id": msg.sender_id,
            "content": msg.content, "media_url": msg.media_url, 
            "media_width": msg.media_width, "media_height": msg.media_height,
            "type": msg.type, "created_at": msg.created_at, "updated_at": msg.updated_at,
            "status": [{"user_id": s.user_id, "delivered_at": s.delivered_at, "read_at": s.read_at} for s in statuses]
        })
    return enriched_messages

async def update_message(db: AsyncSession, *, message_id: str, message_in: MessageUpdate, current_user_id: str) -> Message:
    message = await db.get(Message, message_id)
    if not message: raise NexChatException(status_code=404, detail="Message not found")
    if message.sender_id != current_user_id: raise ForbiddenException(detail="You can only edit your own messages")
    if message_in.content is not None: message.content = message_in.content
    await db.commit()
    await db.refresh(message)
    from app.services import chat_service
    members = await chat_service.get_chat_members(db, chat_id=message.chat_id)
    edit_data = {
        "type": constants.EVENT_MESSAGE_EDIT, 
        "payload": {"id": message.id, "chat_id": message.chat_id, "content": message.content, "updated_at": helpers.format_timestamp(message.updated_at)}
    }
    await manager.broadcast(edit_data, members)
    return message

async def get_message(db: AsyncSession, *, message_id: str) -> Optional[Message]:
    return await message_repo.get_message_by_id(db, message_id=message_id)

async def delete_message(db: AsyncSession, *, message_id: str, current_user_id: str):
    message = await db.get(Message, message_id)
    if not message: raise NexChatException(status_code=404, detail="Message not found")
    if message.sender_id != current_user_id: raise ForbiddenException(detail="Not enough permissions")
    chat_id = message.chat_id
    await message_repo.delete_message(db, message_id=message_id)
    from app.services import chat_service
    members = await chat_service.get_chat_members(db, chat_id=chat_id)
    delete_data = {"type": constants.EVENT_MESSAGE_DELETE, "payload": {"id": message_id, "chat_id": chat_id}}
    await manager.broadcast(delete_data, members)

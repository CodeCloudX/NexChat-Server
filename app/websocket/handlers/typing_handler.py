from typing import Any, Dict
from app.websocket.manager import manager
from app.services import chat_service
from app.infrastructure.database import async_session_maker
from app.schemas.websocket import WSTypingPayload
from app.utils import constants

async def handle_typing(user_id: str, data: Dict[str, Any]):
    """
    Broadcasts typing status with a fail-safe privacy filter.
    Ensures typing works for everyone unless a block is explicitly confirmed.
    """
    try:
        # 1. Validate payload structure
        payload = WSTypingPayload(
            chat_id=data.get("chat_id"),
            user_id=user_id,
            is_typing=data.get("is_typing", False)
        )
    except Exception:
        return 

    async with async_session_maker() as db:
        try:
            # 2. Get members (Efficiency: Service uses Redis cache)
            members = await chat_service.get_chat_members(db, chat_id=payload.chat_id)
            other_members = [m for m in members if m != user_id]
            
            if not other_members:
                return # No one to broadcast to

            # 3. Privacy Check: Only for Direct Chats (Exactly 2 members)
            if len(members) == 2:
                from app.repositories import user_repo
                receiver_id = other_members[0]
                
                # Check for bidirectional blocks
                try:
                    # If either user has blocked the other, suppress the event
                    is_blocked = await user_repo.is_user_blocked(db, blocker_id=user_id, blocked_id=receiver_id) or \
                                 await user_repo.is_user_blocked(db, blocker_id=receiver_id, blocked_id=user_id)
                    
                    if is_blocked:
                        return # Exit early for privacy: Block confirmed
                except Exception:
                    # Fail-open: If DB check fails, we proceed to broadcast 
                    # so we don't break typing for normal users.
                    pass

            # 4. Standard Broadcast
            typing_event = {
                "type": constants.EVENT_TYPING,
                "payload": payload.model_dump()
            }
            await manager.broadcast(typing_event, other_members)
            
        except Exception:
            # Critical handler safety: prevent WS loop from crashing
            pass

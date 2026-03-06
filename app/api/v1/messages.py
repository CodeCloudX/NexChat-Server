from typing import Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.models.user import User
from app.schemas.message import MessageOut, MessageCreate, MessageUpdate
from app.services import message_service

router = APIRouter()

@router.post("/", response_model=MessageOut)
async def send_message(
    *,
    db: AsyncSession = Depends(deps.get_db),
    message_in: MessageCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Send a message. Requires a valid chat_id."""
    return await message_service.send_message(db, message_in=message_in, sender_id=current_user.id)

@router.get("/", response_model=List[MessageOut])
async def read_chat_messages(
    *,
    db: AsyncSession = Depends(deps.get_db),
    chat_id: str = Query(..., description="ID of the chat room"),
    current_user: User = Depends(deps.get_current_user),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
) -> Any:
    """Fetch message history for a chat. Standard query param pattern."""
    return await message_service.get_chat_messages(db, chat_id=chat_id, limit=limit, skip=skip)

@router.patch("/{message_id}", response_model=MessageOut)
async def update_message(
    message_id: str,
    message_in: MessageUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return await message_service.update_message(db, message_id=message_id, message_in=message_in, current_user_id=current_user.id)

@router.delete("/{message_id}")
async def delete_message(
    message_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    await message_service.delete_message(db, message_id=message_id, current_user_id=current_user.id)
    return {"status": "ok"}

from typing import Any, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.schemas.chat import ChatRoomOut, ChatRoomCreate
from app.services import chat_service

router = APIRouter()


@router.post("/", response_model=ChatRoomOut)
async def create_chat_room(
    *,
    db: AsyncSession = Depends(deps.get_db),
    chat_in: ChatRoomCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create or reuse a chat room. Logic handled in chat_service.
    """
    return await chat_service.create_chat_room(db, chat_in=chat_in, creator_id=current_user.id)


@router.get("/", response_model=List[ChatRoomOut])
async def read_user_chats(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
) -> Any:
    """
    Retrieve user's chat rooms with last message and other user info.
    """
    return await chat_service.get_user_chats(
        db, user_id=current_user.id, limit=limit, skip=skip
    )


@router.get("/{chat_id}", response_model=ChatRoomOut)
async def read_chat_by_id(
    chat_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get a specific chat room by id with enriched details.
    """
    return await chat_service.get_enriched_chat(db, chat_id=chat_id, current_user_id=current_user.id)

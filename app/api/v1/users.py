from typing import Any, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate, BlockedUserOut
from app.services import user_service

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def read_user_me(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await user_service.get_user_profile(
        db, 
        target_user_id=current_user.id, 
        current_user_id=current_user.id,
        user_obj=current_user
    )


@router.get("/blocked", response_model=List[BlockedUserOut])
async def read_blocked_users(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return await user_service.get_my_blocked_users(db, user_id=current_user.id)


@router.get("/find-contact", response_model=List[UserOut])
async def find_contact(
    *,
    db: AsyncSession = Depends(deps.get_db),
    email: str = Query(..., description="Partial or full email/name to search for"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Finds contacts matching the query (partial email or name).
    """
    return await user_service.find_contacts_by_query(
        db, query=email, current_user_id=current_user.id
    )


@router.post("/block/{user_id}")
async def block_user(
    user_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    was_blocked = await user_service.block_user(db, blocker_id=current_user.id, blocked_id=user_id)
    if was_blocked:
        return {"status": "ok", "message": "User blocked successfully"}
    return {"status": "ok", "message": "User is already blocked"}


@router.post("/unblock/{user_id}")
async def unblock_user(
    user_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    was_unblocked = await user_service.unblock_user(db, blocker_id=current_user.id, blocked_id=user_id)
    if was_unblocked:
        return {"status": "ok", "message": "User unblocked successfully"}
    return {"status": "ok", "message": "User is not in your blocked list"}


@router.put("/me", response_model=UserOut)
async def update_user_me(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # Any manual update to the profile marks it as 'complete' (dismisses setup screen)
    return await user_service.update_user(db, db_obj=current_user, obj_in=user_in, mark_complete=True)


@router.get("/{user_id}", response_model=UserOut)
async def read_user_by_id(
    user_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    return await user_service.get_user_profile(
        db, target_user_id=user_id, current_user_id=current_user.id
    )

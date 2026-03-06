from typing import Any

from fastapi import APIRouter, Depends, UploadFile, File
from app.api import deps
from app.models.user import User
from app.services import user_service, media_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/profile-photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Route to handle profile photo upload.
    """
    url = await user_service.update_profile_photo(db, user=current_user, file=file)
    return {"url": url}


@router.post("/media")
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Route to handle chat media upload.
    Now returns width and height to help fix frontend CLS issues.
    """
    url, mime_type, size, width, height = await media_service.upload_chat_media(
        user_id=current_user.id, 
        file=file
    )
    return {
        "url": url, 
        "mime_type": mime_type, 
        "size": size,
        "width": width,
        "height": height
    }

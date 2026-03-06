from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None


class UserOut(UserBase):
    id: str
    bio: Optional[str] = None
    profile_photo_url: Optional[str] = None
    is_active: bool
    is_profile_complete: bool = False
    is_online: bool = False  # Real-time status from Redis
    last_seen: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BlockedUserOut(BaseModel):
    """
    Simplified user info for the blocked list.
    Includes just enough to identify and unblock the user.
    """
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    profile_photo_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

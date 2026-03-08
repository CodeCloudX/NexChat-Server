from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    session_id: str
    token_type: str = "bearer"
    is_profile_complete: bool = False


class GoogleLogin(BaseModel):
    id_token: str
    device_id: str
    device_name: Optional[str] = None
    platform: Optional[str] = "android"


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str
    device_id: str
    device_name: Optional[str] = None
    platform: Optional[str] = "android"

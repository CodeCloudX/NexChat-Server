from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str
    is_profile_complete: bool = False


class TokenPayload(BaseModel):
    sub: Optional[str] = None


class GoogleLogin(BaseModel):
    """Schema for Google Sign-In via Firebase ID Token."""
    id_token: str


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str

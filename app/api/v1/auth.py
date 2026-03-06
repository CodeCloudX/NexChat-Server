from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core import security
from app.core.config import settings
from app.schemas.auth import Token, GoogleLogin, OTPRequest, OTPVerify
from app.services import user_service, otp_service

router = APIRouter()


@router.post("/otp/request")
async def request_otp(
    *,
    db: AsyncSession = Depends(deps.get_db),
    otp_in: OTPRequest,
) -> Any:
    """
    Generate and send OTP to email. 
    Works for both new and existing users (Passwordless).
    """
    await otp_service.generate_otp(otp_in.email)
    return {"message": "OTP sent to email (check logs in dev)"}


@router.post("/otp/verify", response_model=Token)
async def verify_otp_login(
    *,
    db: AsyncSession = Depends(deps.get_db),
    otp_in: OTPVerify,
) -> Any:
    """
    Verify OTP and return access token.
    Creates user if not exists (Sign-in/Sign-up in one go).
    """
    is_valid = await otp_service.verify_otp(otp_in.email, otp_in.otp)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    user = await user_service.get_user_by_email(db, email=otp_in.email)
    
    if not user:
        # Create naya user agar pehle se nahi hai (Sign-up)
        user = await user_service.create_passwordless_user(db, email=otp_in.email)
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "is_profile_complete": user.is_profile_complete
    }


@router.post("/google", response_model=Token)
async def login_google(
    *,
    db: AsyncSession = Depends(deps.get_db),
    login_in: GoogleLogin,
) -> Any:
    """
    Login or Register via Google using Firebase ID Token.
    """
    from app.services import auth_service
    user = await auth_service.authenticate_google(db, id_token=login_in.id_token)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "is_profile_complete": user.is_profile_complete
    }

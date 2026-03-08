from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.schemas.auth import Token, GoogleLogin, OTPRequest, OTPVerify
from app.services import user_service, otp_service, session_service

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
    return {"message": "OTP sent to email."}


@router.post("/otp/verify", response_model=Token)
async def verify_otp_login(
    *,
    db: AsyncSession = Depends(deps.get_db),
    otp_in: OTPVerify,
    request: Request
) -> Any:
    """
    Verify OTP and return Session ID.
    Creates user if not exists. Enforces single device login.
    """
    is_valid = await otp_service.verify_otp(otp_in.email, otp_in.otp)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    user = await user_service.get_user_by_email(db, email=otp_in.email)
    
    if not user:
        user = await user_service.create_passwordless_user(db, email=otp_in.email)
        
    # Start new session
    new_session = await session_service.start_session(
        db,
        user_id=user.id,
        device_id=otp_in.device_id,
        device_name=otp_in.device_name,
        ip_address=request.client.host,
        platform=otp_in.platform
    )
    
    return {
        "session_id": new_session.id,
        "token_type": "bearer",
        "is_profile_complete": user.is_profile_complete
    }


@router.post("/google", response_model=Token)
async def login_google(
    *,
    db: AsyncSession = Depends(deps.get_db),
    login_in: GoogleLogin,
    request: Request
) -> Any:
    """
    Login or Register via Google using Firebase ID Token.
    Returns Session ID and enforces single device.
    """
    from app.services import auth_service
    user = await auth_service.authenticate_google(db, id_token=login_in.id_token)
    
    # Start new session
    new_session = await session_service.start_session(
        db,
        user_id=user.id,
        device_id=login_in.device_id,
        device_name=login_in.device_name,
        ip_address=request.client.host,
        platform=login_in.platform
    )
    
    return {
        "session_id": new_session.id,
        "token_type": "bearer",
        "is_profile_complete": user.is_profile_complete
    }


@router.delete("/logout")
async def logout(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
    request: Request
) -> Any:
    """
    Invalidates the current session.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Session "):
        session_id = auth_header.replace("Session ", "")
        await session_service.end_session(db, session_id)
    
    return {"status": "ok", "message": "Logged out successfully"}

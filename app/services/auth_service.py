from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from firebase_admin import auth as firebase_auth

from app.models.user import User
from app.repositories import user_repo
from app.services import user_service
from app.core.exceptions import AuthenticationException, InactiveUserException


async def authenticate_google(
    db: AsyncSession, *, id_token: str
) -> User:
    """
    Verifies Firebase ID Token from Google Sign-In.
    Creates user if not exists. (Passwordless)
    """
    try:
        # 1. Verify the token with Firebase
        decoded_token = firebase_auth.verify_id_token(id_token)
        email = decoded_token.get("email")
        full_name = decoded_token.get("name")
        photo_url = decoded_token.get("picture")

        if not email:
            raise AuthenticationException(detail="Email not provided by Google")

        # 2. Check if user already exists
        user = await user_repo.get_user_by_email(db, email=email)

        if not user:
            # 3. Create a new user for Google Sign-In (Passwordless)
            user = await user_service.create_passwordless_user(
                db,
                email=email,
                full_name=full_name
            )

            # Update profile photo from Google if available
            if photo_url:
                await user_service.update_user(db, db_obj=user, obj_in={"profile_photo_url": photo_url}, mark_complete=False)
        
        if not user.is_active:
            raise InactiveUserException()

        return user
        
    except Exception as e:
        raise AuthenticationException(detail=f"Google authentication failed: {str(e)}")

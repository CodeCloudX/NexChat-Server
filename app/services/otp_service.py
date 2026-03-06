import logging
from app.infrastructure.redis import redis_client
from app.utils.helpers import generate_otp_code
from app.utils.constants import OTP_TTL, OTP_LENGTH, OTP_MAX_ATTEMPTS, OTP_COOLDOWN
from app.core.exceptions import NexChatException
from app.services import email_service

logger = logging.getLogger(__name__)

async def generate_otp(email: str) -> str:
    """
    Generates an OTP, stores it in Redis, and sends it via email.
    Strictly prevents multiple active OTPs to reduce server load.
    """
    # 1. Check if user is blocked (6 hours)
    is_blocked = await redis_client.get(f"otp_blocked:{email}")
    if is_blocked:
        raise NexChatException(status_code=429, detail="Too many attempts. Locked for 6 hours.")

    # 2. Check if an active OTP already exists
    existing_otp = await redis_client.get(f"otp:{email}")
    if existing_otp:
        raise NexChatException(
            status_code=400, 
            detail="An active OTP already exists. Please check your inbox or wait for it to expire."
        )

    # 3. Check and increment attempt count
    attempts = await redis_client.get(f"otp_attempts:{email}")
    attempts = int(attempts) if attempts else 0
    
    if attempts >= OTP_MAX_ATTEMPTS:
        await redis_client.set(f"otp_blocked:{email}", "1", expire=OTP_COOLDOWN)
        await redis_client.delete(f"otp_attempts:{email}")
        raise NexChatException(status_code=429, detail="Maximum OTP requests reached. Blocked for 6 hours.")

    # 4. Generate and store NEW OTP
    otp = generate_otp_code(OTP_LENGTH)
    await redis_client.set(f"otp:{email}", otp, expire=OTP_TTL)
    
    # 5. Send OTP via Email
    # Note: We send the email *after* storing in Redis to ensure verification works immediately
    email_sent = await email_service.send_otp_email(email, otp)
    if not email_sent:
        # If email fails, we might want to log it, but in dev it just prints to console
        logger.warning(f"Failed to send OTP email to {email}")

    # 6. Increment attempts
    await redis_client.set(f"otp_attempts:{email}", str(attempts + 1), expire=OTP_COOLDOWN)
    
    logger.info(f"New OTP generated and sent to {email}")
    return otp

async def verify_otp(email: str, otp: str) -> bool:
    """Verifies the OTP and clears attempts on success."""
    stored_otp = await redis_client.get(f"otp:{email}")
    if stored_otp and stored_otp == otp:
        await redis_client.delete(f"otp:{email}")
        await redis_client.delete(f"otp_attempts:{email}")
        return True
    return False

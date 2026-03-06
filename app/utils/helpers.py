import uuid
import random
from datetime import datetime, timezone

def generate_uuid() -> str:
    """Generates a unique string UUID."""
    return str(uuid.uuid4())

def generate_otp_code(digits: int = 6) -> str:
    """Generates a numeric OTP code of specified length."""
    return "".join([str(random.randint(0, 9)) for _ in range(digits)])

def get_now() -> datetime:
    """Returns current UTC timestamp."""
    return datetime.now(timezone.utc)

def get_filename_extension(filename: str) -> str:
    """Extracts extension from a filename."""
    if "." in filename:
        return filename.split(".")[-1].lower()
    return ""

def format_timestamp(dt: datetime) -> str:
    """Standardizes datetime formatting for JSON responses."""
    if not dt:
        return None
    return dt.isoformat()

import asyncio
import logging
from typing import List, Optional
from app.infrastructure.push import send_multicast_notification

logger = logging.getLogger(__name__)

async def send_notification_task(tokens: List[str], title: str, body: str, data: Optional[dict] = None):
    """
    Background task to send push notifications.
    Using background tasks ensures the API stays fast and responsive.
    """
    if not tokens:
        return
    try:
        # Firebase handles the delivery logic
        await send_multicast_notification(tokens, title, body, data)
        logger.info(f"Notification successfully queued for {len(tokens)} devices.")
    except Exception as e:
        logger.error(f"Failed to send background notifications: {e}")

async def cleanup_old_data_task():
    """
    Periodic maintenance task. 
    Can be used for clearing old logs or temporary files.
    Redis presence is handled via TTL, so no manual cleanup needed here.
    """
    while True:
        try:
            # Example: Clear temp logs or audit entries older than 30 days
            await asyncio.sleep(86400) # Run once a day
        except Exception as e:
            logger.error(f"Maintenance task error: {e}")
            await asyncio.sleep(3600)

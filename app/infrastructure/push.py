import firebase_admin
from firebase_admin import credentials, messaging
from typing import List, Optional
from app.core.config import settings

def init_firebase():
    """Initializes Firebase Admin SDK safely."""
    if settings.FIREBASE_CREDENTIALS:
        # Prevent re-initialization if app already exists
        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
            firebase_admin.initialize_app(cred)

async def send_push_notification(token: str, title: str, body: str, data: Optional[dict] = None):
    """Sends a push notification to a single device via FCM V1."""
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data,
        token=token,
    )
    try:
        return messaging.send(message)
    except Exception:
        return None

async def send_multicast_notification(tokens: List[str], title: str, body: str, data: Optional[dict] = None):
    """Sends a push notification to multiple devices via FCM V1."""
    if not tokens:
        return None
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data=data,
        tokens=tokens,
    )
    try:
        return messaging.send_multicast(message)
    except Exception:
        return None

from typing import Optional, Dict, Any
from pydantic import BaseModel


class NotificationTokenCreate(BaseModel):
    """
    Schema for registering or updating a user's FCM device token.
    """
    token: str
    platform: Optional[str] = "android" # e.g., android, ios, web


class NotificationPayload(BaseModel):
    """
    Internal schema for defining notification content.
    """
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    """
    Standard response after token registration.
    """
    status: str = "ok"
    message: str

import logging
from typing import Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

async def send_email(
    email_to: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Sends email via Brevo REST API (HTTP). 
    Safe for Render Free Tier.
    """
    if not settings.BREVO_API_KEY:
        logger.warning(f"Skipping email to {email_to} - BREVO_API_KEY missing.")
        print(f"DEBUG EMAIL to {email_to}: {subject}\nContent: {html_content}")
        return False

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json"
    }
    data = {
        "sender": {"name": settings.EMAILS_FROM_NAME, "email": settings.EMAILS_FROM_EMAIL},
        "to": [{"email": email_to}],
        "subject": subject,
        "htmlContent": html_content,
    }
    if text_content:
        data["textContent"] = text_content

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=data)
            if response.status_code <= 201:
                logger.info(f"Email sent successfully to {email_to} via Brevo")
                return True
            logger.error(f"Brevo API Error: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            logger.error(f"Brevo HTTP Error: {e}")
            return False

async def send_otp_email(email_to: str, otp: str) -> bool:
    """Sends a styled OTP email to the user via Brevo."""
    subject = f"NexChat verification code: {otp}"
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px; text-align: center;">
                <h2 style="color: #4f46e5;">NexChat Verification</h2>
                <p>Hello,</p>
                <p>Use the following code to sign in to your account. Valid for 5 minutes.</p>
                <div style="background: #f3f4f6; padding: 20px; font-size: 32px; font-weight: bold; color: #4f46e5; border-radius: 8px; margin: 20px 0;">
                    {otp}
                </div>
                <p style="font-size: 10px; color: #999;">&copy; 2026 NexChat. All rights reserved.</p>
            </div>
        </body>
    </html>
    """
    
    text_content = f"Your NexChat verification code is: {otp}. Valid for 5 minutes."

    return await send_email(email_to, subject, html_content, text_content)

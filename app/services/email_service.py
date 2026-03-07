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
    """Sends a professional NexChat branded OTP email based on simplified dark theme."""
    subject = f"NexChat verification code: {otp}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: #000000;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }}
            .container {{
                max-width: 400px;
                margin: 40px auto;
                background-color: #121212;
                border-radius: 16px;
                border: 1px solid #222222;
                padding: 40px 20px;
                text-align: center;
                color: #ffffff;
            }}
            .title {{
                font-size: 22px;
                font-weight: 700;
                color: #a78bfa;
                margin-bottom: 24px;
            }}
            .instruction {{
                font-size: 14px;
                color: #aaaaaa;
                line-height: 1.5;
                margin-bottom: 30px;
            }}
            .otp-box {{
                background-color: #1e1e1e;
                padding: 25px;
                border-radius: 12px;
                font-size: 40px;
                font-weight: 700;
                color: #a78bfa;
                letter-spacing: 5px;
                margin-bottom: 30px;
                display: inline-block;
                width: 80%;
            }}
            .footer {{
                font-size: 12px;
                color: #666666;
                margin-top: 20px;
            }}
            .branding {{
                margin-top: 10px;
                font-weight: 600;
                color: #888888;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="title">NexChat Verification</div>
            
            <div class="instruction">
                Use the following code to sign in to your account. Valid for 5 minutes.
            </div>
            
            <div class="otp-box">
                {otp}
            </div>
            
            <div class="footer">
                If you did not request this code, please ignore this email.
            </div>
            
            <div class="branding">
                NexChat by CodeCloudX
            </div>
            
            <div style="font-size: 10px; color: #444; margin-top: 20px;">
                &copy; 2026 NexChat. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"Your NexChat verification code is: {otp}. It expires in 5 minutes. NexChat by CodeCloudX"

    return await send_email(email_to, subject, html_content, text_content)

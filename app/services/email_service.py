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
    """Sends a professional NexChat branded OTP email."""
    subject = f"{otp} is your NexChat verification code"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            .container {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 500px;
                margin: 0 auto;
                padding: 40px 20px;
                color: #1f2937;
                background-color: #f9fafb;
            }}
            .card {{
                background-color: #ffffff;
                padding: 32px;
                border-radius: 16px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                text-align: center;
            }}
            .logo {{
                color: #4f46e5;
                font-size: 28px;
                font-weight: 800;
                margin-bottom: 24px;
                letter-spacing: -0.025em;
            }}
            .title {{
                font-size: 20px;
                font-weight: 600;
                color: #111827;
                margin-bottom: 8px;
            }}
            .subtitle {{
                font-size: 14px;
                color: #6b7280;
                margin-bottom: 32px;
            }}
            .otp-box {{
                background-color: #f3f4f6;
                padding: 24px;
                font-size: 36px;
                font-weight: 700;
                color: #4f46e5;
                letter-spacing: 8px;
                border-radius: 12px;
                margin-bottom: 32px;
                border: 1px solid #e5e7eb;
            }}
            .footer {{
                margin-top: 32px;
                font-size: 12px;
                color: #9ca3af;
                line-height: 1.5;
            }}
            .warning {{
                font-size: 12px;
                color: #9ca3af;
                margin-top: 16px;
                padding-top: 16px;
                border-top: 1px solid #f3f4f6;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="logo">NexChat</div>
                <div class="title">Verification Code</div>
                <div class="subtitle">Please use the following code to sign in to your account.</div>
                
                <div class="otp-box">
                    {otp}
                </div>
                
                <div class="footer">
                    This code will expire in <strong>5 minutes</strong>.<br>
                    If you did not request this code, please ignore this email.
                </div>
                
                <div class="warning">
                    Securely connecting people.<br>
                    &copy; 2026 NexChat Team.
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"Your NexChat verification code is: {otp}. It expires in 5 minutes."

    return await send_email(email_to, subject, html_content, text_content)

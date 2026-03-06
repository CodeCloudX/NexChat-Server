import logging
import smtplib
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anyio  # FastAPI uses anyio for thread pools

from app.core.config import settings

logger = logging.getLogger(__name__)

def _send_smtp_sync(
    email_to: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Blocking SMTP logic to be run in a background thread.
    """
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        message["To"] = email_to

        if text_content:
            message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM_EMAIL, email_to, message.as_string())
        
        return True
    except Exception as e:
        logger.error(f"SMTP Error for {email_to}: {str(e)}")
        return False

async def send_email(
    email_to: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Asynchronously sends an email by offloading the blocking SMTP call
    to a separate thread pool.
    """
    if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
        logger.warning(f"Skipping email to {email_to} - SMTP settings missing.")
        print(f"DEBUG EMAIL to {email_to}: {subject}\nContent: {html_content}")
        return False

    # anyio.to_thread.run_sync runs the blocking function in a thread pool
    return await anyio.to_thread.run_sync(
        _send_smtp_sync, email_to, subject, html_content, text_content
    )

async def send_otp_email(email_to: str, otp: str) -> bool:
    """Sends a styled OTP email to the user."""
    subject = f"NexChat verification code: {otp}"
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                <h2 style="color: #4f46e5; text-align: center;">NexChat Verification</h2>
                <p>Hello,</p>
                <p>Use the following code to sign in to your NexChat account. This code is valid for 5 minutes.</p>
                <div style="background: #f3f4f6; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #4f46e5; border-radius: 8px; margin: 20px 0;">
                    {otp}
                </div>
                <p style="font-size: 12px; color: #666; text-align: center;">
                    If you didn't request this code, you can safely ignore this email.
                </p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 10px; color: #999; text-align: center;">
                    &copy; 2026 NexChat. All rights reserved.
                </p>
            </div>
        </body>
    </html>
    """
    
    text_content = f"Your NexChat verification code is: {otp}. It expires in 5 minutes."
    
    return await send_email(email_to, subject, html_content, text_content)

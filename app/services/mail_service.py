"""Mail service for sending emails.

Uses fastapi-mail to send emails using SMTP configuration.
"""

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings
from pydantic import EmailStr
from typing import List


class MailService:
    """Service for sending emails via SMTP."""

    def __init__(self):
        """Initialize FastMail with configuration."""
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.SMTP_USER,
            MAIL_PASSWORD=settings.SMTP_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.SMTP_PORT,
            MAIL_SERVER=settings.SMTP_HOST,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        self.mail = FastMail(self.conf)

    async def send_email(self, target_email: EmailStr, subject: str, content: str):
        """Send an email with the given content.

        Args:
            target_email: Recipient email address.
            subject: Email subject.
            content: Email body content.
        """
        message = MessageSchema(
            subject=subject,
            recipients=[target_email],
            body=content,
            subtype=MessageType.html
        )
        
        await self.mail.send_message(message)


# Singleton instance
mail_service = MailService()

import logging
from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.conf.config import settings
from src.services.auth_service import AuthService

__all__ = ["EmailService"]

logger = logging.getLogger(__name__)


class EmailService:
    conf = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=settings.USE_CREDENTIALS,
        VALIDATE_CERTS=settings.VALIDATE_CERTS,
        TEMPLATE_FOLDER=Path(__file__).parent / "templates",
    )
    auth_service = AuthService()

    async def send_verification_email(self, email: EmailStr, username: str, host: str):
        """
        Sends an email for account verification.
        """
        try:
            token_verification = self.auth_service.create_email_token({"sub": email})
            message = MessageSchema(
                subject="Confirm your email",
                recipients=[email],
                template_body={
                    "host": host,
                    "username": username,
                    "token": token_verification,
                },
                subtype=MessageType.html,
            )

            fm = FastMail(self.conf)
            await fm.send_message(message, template_name="verify_email.html")
        except ConnectionErrors as e:
            logger.warning("Failed to send email: %s", e)

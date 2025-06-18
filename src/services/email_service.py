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
    """
    A service class for handling all email-related functionalities.

    This class manages the configuration for connecting to an SMTP server
    and provides methods for sending different types of application emails,
    such as account verification emails.
    """

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
        Sends an email to a user for account verification.

        This method generates a unique JWT for email verification, constructs the
        email message using an HTML template, and sends it. It includes error
        handling to log connection issues without crashing the parent process.

        Args:
            email (EmailStr): The recipient's email address.
            username (str): The recipient's username, used for personalization.
            host (str): The base URL of the application, used to construct the
                        verification link.
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

    async def send_password_reset_email(
        self, email: EmailStr, username: str, host: str, token: str
    ):
        """Sends an email with a password reset link.

        This method constructs and sends an HTML email containing a unique,
        time-sensitive token for the user to reset their password.

        Args:
            email (EmailStr): The email address of the recipient.
            username (str): The username of the recipient for personalization.
            host (str): The base URL of the application, used to construct the link.
            token (str): The password reset JWT.
        """
        try:
            message = MessageSchema(
                subject="Password Reset Request",
                recipients=[email],
                template_body={
                    "host": host,
                    "username": username,
                    "token": token,
                },
                subtype=MessageType.html,
            )

            fm = FastMail(self.conf)
            await fm.send_message(message, template_name="password_reset.html")
        except ConnectionErrors as err:
            logger.error("Failed to send password reset email: %s", err)

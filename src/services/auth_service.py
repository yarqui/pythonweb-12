from __future__ import annotations

from datetime import datetime, timedelta, timezone, UTC
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import settings
from src.database.db import get_db
from src.repository import UserRepository

__all__ = ["AuthService", "get_current_user"]


class AuthService:
    """
    A service class responsible for all authentication-related logic,
    including password hashing, token creation, and token decoding.
    """

    # Password Hashing Setup
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # OAuth2 Scheme Setup
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies a plain-text password against its hashed version.

        :param plain_password: The plain-text password to check.
        :param hashed_password: The stored hashed password to compare against.
        :return: True if the passwords match, False otherwise.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        """
        Hashes a plain-text password using the configured bcrypt scheme.

        :param password: The plain-text password to hash.
        :return: The resulting hashed password string.
        """
        return self.pwd_context.hash(password)

    async def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Hashes a plain-text password using the configured bcrypt scheme.

        :param password: The plain-text password to hash.
        :return: The resulting hashed password string.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "scope": "access_token",  # Scope to identify this as an access token
            }
        )
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    async def create_refresh_token(self, data: dict) -> str:
        """
        Hashes a plain-text password using the configured bcrypt scheme.

        :param password: The plain-text password to hash.
        :return: The resulting hashed password string.
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "scope": "refresh_token",  # Scope for refresh token
            }
        )
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    async def decode_refresh_token(self, refresh_token: str) -> str:
        """
        Decodes and validates a refresh token.

        :param refresh_token: The refresh token to decode.
        :return: The user's email address (the token's subject).
        :raises HTTPException: If the token is invalid, expired, or has the wrong scope.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
        try:
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            if payload.get("scope") == "refresh_token":
                email = payload.get("sub")

                if email is None:
                    raise credentials_exception
                return email

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError as e:
            raise credentials_exception from e

    def create_email_token(self, data: dict) -> str:
        """
        Creates a short-lived JWT specifically for email verification.

        :param data: The payload data, typically containing the user's email.
        :return: The encoded JWT for email verification.
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(hours=48)
        to_encode.update({"exp": expire, "scope": "email_verification"})
        token = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return token

    async def decode_email_token(self, token: str) -> str:
        """
        Decodes and validates an email verification token.

        :param token: The verification token from the email link.
        :return: The user's email address (the token's subject).
        :raises HTTPException: If the token is invalid, expired, or has the wrong scope.
        """
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            if payload.get("scope") == "email_verification":
                email = payload.get("sub")

                if email is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token for email verification",
                    )

                return email

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for email verification",
            ) from e

    async def login_user(
        self, body: OAuth2PasswordRequestForm, db: AsyncSession
    ) -> dict:
        """
        Handles the complete user login process.

        Verifies user credentials, checks for email verification, and generates access
        and refresh tokens upon successful authentication.

        :param body: The form data containing username and password.
        :param db: The database session.
        :return: A dictionary containing access and refresh tokens.
        :raises HTTPException: If authentication fails or the email is not verified.
        """
        user_repo = UserRepository(db)

        if "@" in body.username:
            user = await user_repo.get_user_by_email(body.username)
        else:
            user = await user_repo.get_user_by_username(body.username)

        if user is None or not self.verify_password(
            body.password, user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        if not user.verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified"
            )

        access_token = await self.create_access_token(data={"sub": user.email})
        refresh_token = await self.create_refresh_token(data={"sub": user.email})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }


async def get_current_user(
    request: Request,
    token: str = Depends(AuthService.oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    A FastAPI dependency that authenticates a user via a JWT access token.

    It decodes the token, validates its scope, and fetches the corresponding user
    from the database. If any step fails, it raises a 401 Unauthorized error.
    Attaches the user object to the request state for rate limiting.

    :param token: The JWT access token from the 'Authorization: Bearer' header.
    :param db: The database session dependency.
    :param request: The FastAPI request object.
    :return: The authenticated User ORM object.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("scope") != "access_token":
            raise credentials_exception

        email = payload.get("sub")

        if email is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception from e

    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_email(email)

    if user is None:
        raise credentials_exception

    request.state.user = user
    return user

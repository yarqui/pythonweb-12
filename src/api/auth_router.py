from fastapi import APIRouter, Depends, status, Request, BackgroundTasks, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import redis

from src.database.db import get_db, get_redis_client
from src.schemas import (
    UserCreate,
    UserResponse,
    TokenResponse,
    RequestEmail,
    ResetPasswordForm,
    PasswordResetRequest,
)
from src.services import (
    UserService,
    AuthService,
    EmailService,
    get_auth_service,
    get_user_service,
)
from src.repository import UserRepository

auth_router = APIRouter(prefix="/auth", tags=["authentication"])


@auth_router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def signup(
    body: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    user_service: UserService = Depends(get_user_service),
):
    """
    Handles user registration. The service layer contains all business logic,
    including checking for existing users. The router just calls the service.
    """
    new_user = await user_service.create_user(body, background_tasks, request)
    return new_user


@auth_router.post("/login", response_model=TokenResponse, summary="User Login")
async def login(
    body: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    """
    Handles user login,caches the user object and provides access and refresh tokens.

    This endpoint authenticates a user based on a username and password submitted
    in a standard OAuth2 form. On successful authentication, it returns a JWT
    access token and a refresh token.

    Returns:
        A dictionary containing the access token, refresh token, and token type.
    """
    return await auth_service.login_user(body, db, redis_client)


@auth_router.post(
    "/request-password-reset",
    status_code=status.HTTP_200_OK,
    summary="Request a Password Reset",
)
async def request_password_reset(
    body: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(EmailService),
):
    """
    Handles a request to send a password reset email.

    If a user with the given email exists, a background task is triggered
    to send an email with a password reset token. Always returns a generic
    success message to prevent email enumeration attacks.
    """
    user = await user_service.get_user_by_email(body.email)
    if user:
        token = auth_service.create_password_reset_token(data={"sub": user.email})
        background_tasks.add_task(
            email_service.send_password_reset_email,
            user.email,
            user.username,
            str(request.base_url),
            token,
        )
    return {
        "message": "If an account with this email exists, a password reset link has been sent."
    }


@auth_router.post(
    "/reset-password", status_code=status.HTTP_200_OK, summary="Reset User Password"
)
async def reset_password(
    body: ResetPasswordForm,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Resets the user's password using a valid token.
    """
    email = await auth_service.decode_password_reset_token(body.token)
    updated_user = await user_service.reset_password(email, body.new_password)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return {"message": "Your password has been reset successfully."}


@auth_router.get("/verified_email/{token}")
async def verified_email(
    token: str,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Verifies a user's email address using a secure, time-sensitive token.

    This endpoint is the target for the verification link sent to a user's email
    after they sign up. It decodes the provided JWT, finds the corresponding user,
    and updates their `verified` status in the database.

    Args:
        token (str): The verification token from the URL path.
        user_service (UserService): The dependency for user-related business logic.
        auth_service (AuthService): The dependency for token-decoding logic.

    Raises:
        HTTPException (400 Bad Request): If the token is valid but points to a
                                         non-existent user.
        HTTPException (422 Unprocessable Entity): If the token is malformed, invalid,
                                                  or expired.

    Returns:
        A dictionary with a confirmation message, indicating either successful
        verification or that the email had already been verified.
    """

    email = await auth_service.decode_email_token(token)
    user = await user_service.get_user_by_email(email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.verified:
        return {"message": "Your email is already verified."}

    await user_service.confirm_email(email)
    return {"message": "Email confirmed successfully."}


@auth_router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handles requests to re-send an email verification link.

    This endpoint finds a user by their email. If the user exists and is not
    already verified, it triggers a background task to send a new verification
    email. To prevent user enumeration attacks, it returns a generic success
    message whether the user was found or not.

    Args:
        body (RequestEmail): The request body containing the user's email address.
        background_tasks (BackgroundTasks): FastAPI's mechanism for running tasks
                                           after returning a response, used here to
                                           send the email without blocking.
        request (Request): The standard FastAPI request object, used to get the
                           base URL for constructing the verification link.
        db (AsyncSession): The database session dependency.

    Returns:
        A dictionary with a confirmation message. This will either state that the
        email is already verified, or provide a generic message indicating that
        an email has been sent if an account exists.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_email(body.email)

    if user and user.verified:
        return {"message": "Your email is already verified."}
    if user:
        email_service = EmailService()
        background_tasks.add_task(
            email_service.send_verification_email,
            user.email,
            user.username,
            str(request.base_url),
        )
    return {"message": "Check your email for the verification link."}

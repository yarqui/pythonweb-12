from fastapi import APIRouter, Depends, status, Request, BackgroundTasks, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.schemas import UserCreate, UserResponse, TokenResponse, RequestEmail
from src.services import (
    get_user_service,
    UserService,
    AuthService,
    get_auth_service,
    EmailService,
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
):
    return await auth_service.login_user(body, db)


@auth_router.get("/verified_email/{token}")
async def verified_email(token: str, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService()
    user_repo = UserRepository(db)

    email = await auth_service.decode_email_token(token)
    user = await user_repo.get_user_by_email(email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.verified:
        return {"message": "Your email is already verified."}

    await user_repo.confirm_email(email)
    return {"message": "Email confirmed successfully."}


@auth_router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
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

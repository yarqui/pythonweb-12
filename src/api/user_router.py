from fastapi import APIRouter, Depends, Request, File, UploadFile
from fastapi.concurrency import run_in_threadpool

from src.schemas import UserResponse

from src.database.models import User

from src.services import (
    get_current_user,
    get_user_service,
    upload_file,
    UserService,
)
from src.services import limiter

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User's Profile",
)
@limiter.limit("5/minute")
async def get_own_profile(
    request: Request, current_user: User = Depends(get_current_user)
):
    return current_user


@user_router.patch("/avatar", response_model=UserResponse, summary="Update Avatar")
async def update_avatar_user(
    file: UploadFile = File(),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):

    avatar_url = await run_in_threadpool(upload_file, file, current_user.username)

    updated_user = await user_service.update_avatar_url(current_user.email, avatar_url)

    return updated_user

from fastapi import APIRouter, Depends, Request, File, UploadFile, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from src.enums.roles import Role
from src.schemas import UserResponse
from src.database.models import User
from src.services import (
    get_current_user,
    get_user_service,
    upload_file,
    UserService,
    RoleAccessService,
)
from src.services import limiter

user_router = APIRouter(prefix="/users", tags=["users"])

is_admin = RoleAccessService(allowed_roles=[Role.ADMIN])


@user_router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User's Profile",
)
@limiter.limit("5/minute")
async def get_own_profile(
    request: Request, current_user: User = Depends(get_current_user)
):
    """
    Retrieves the profile information for the currently authenticated user.

    This endpoint requires a valid JWT access token in the Authorization header.
    It uses the `get_current_user` dependency to validate the token and fetch
    the corresponding user from the database. The rate limit is applied per user.

    Args:
        request (Request): The request object, required by the rate limiter.
        current_user (User): The authenticated user object, injected by the dependency.

    Returns:
        UserResponse: The authenticated user's profile information.
    """
    return current_user


@user_router.patch(
    "/avatar",
    response_model=UserResponse,
    summary="Update Avatar",
    dependencies=[Depends(is_admin)],
)
async def update_avatar_user(
    file: UploadFile = File(),
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Updates the avatar for the currently authenticated user.

    The user must provide an image file in a multipart/form-data request.
    The file is uploaded to a cloud service, and the resulting URL is saved
    to the user's profile in the database.

    Args:
        file (UploadFile): The image file to be uploaded.
        current_user (User): The authenticated user object, injected by the dependency.
        user_service (UserService): The dependency for user-related business logic.

    Raises:
        HTTPException (403 Forbidden): If the user does not have the 'admin' role.
        HTTPException (404 Not Found): If the current authenticated user is not
                                       found in the database during the update operation.

    Returns:
        UserResponse: The updated user profile with the new avatar URL.
    """

    contents = await file.read()
    avatar_url = await run_in_threadpool(upload_file, contents, current_user.username)

    updated_user = await user_service.update_avatar_url(current_user.email, avatar_url)
    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return updated_user

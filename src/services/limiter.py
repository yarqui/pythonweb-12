from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


__all__ = ["limiter"]


def get_limiter_key(request: Request) -> str:
    """
    Determines the unique identifier for an incoming request for rate limiting.

    The function prioritizes the authenticated user's ID if available on the
    request state. If no authenticated user is found, it falls back to using
    the client's remote IP address. This allows for per-user rate limiting on
    protected routes and per-IP limiting on public routes.

    Args:
        request (Request): The incoming FastAPI request object.

    Returns:
        str: A string identifier for the client (either user ID or IP address).
    """
    if hasattr(request.state, "user"):
        return str(request.state.user.id)
    return get_remote_address(request)


limiter = Limiter(key_func=get_limiter_key)

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


__all__ = ["limiter"]


def get_limiter_key(request: Request) -> str:
    """
    Defines the key for rate limiting. Prioritizes the authenticated user,
    falls back to IP address for anonymous requests.
    """
    if hasattr(request.state, "user"):
        return str(request.state.user.id)
    return get_remote_address(request)


limiter = Limiter(key_func=get_limiter_key)

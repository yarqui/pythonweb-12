from ipaddress import ip_address
from typing import Callable

import cloudinary
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from slowapi.errors import RateLimitExceeded

from src.services import limiter
from src.api import contact_router, health_router, auth_router, user_router
from src.conf.config import get_settings

settings = get_settings()


# Configure the Cloudinary library with credentials from the settings.
# This is done once when the application starts.
cloudinary.config(
    cloud_name=settings.CLOUDINARY_API_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

# Load CORS origins and banned IPs from the central config.
origins = settings.ALLOWED_ORIGINS
banned_ips = settings.BANNED_IPS

app = FastAPI()

# Attach the rate limiter instance to the application's state.
app.state.limiter = limiter

# Add CORS middleware to allow cross-origin requests from specified domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def ban_ips_middleware(request: Request, call_next: Callable):
    """
    A global middleware to block requests from a predefined list of banned IP addresses.

    This function intercepts every incoming HTTP request. It checks the client's IP
    address against a banned list. If a match is found, it immediately returns a
    403 Forbidden response. Otherwise, it passes the request to the next
    handler in the middleware stack.

    Args:
        request (Request): The incoming request object.
        call_next (Callable): A function that receives the request and calls the
                           next middleware or the actual endpoint.

    Returns:
        Response: A JSONResponse with a 403 status if the IP is banned, or the
                  response from the actual endpoint if the IP is allowed.
    """
    if request.client and request.client.host:
        try:
            ip = ip_address(request.client.host)
            if ip in banned_ips:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "You are banned from accessing this resource."},
                )
        except ValueError:
            pass
    response = await call_next(request)
    return response


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom global exception handler for rate limit exceeded errors.

    This handler is triggered by the `slowapi` limiter when a client exceeds
    their configured request limit. It returns a standardized 429 Too Many
    Requests response.

    Args:
        request (Request): The request object that triggered the rate limit.
        exc (RateLimitExceeded): The exception instance raised by slowapi.

    Returns:
        JSONResponse: A JSON response with a 429 status code and an error detail message.
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Too many requests. Please try again later"},
    )


# Include all modular API routers with a common versioned prefix
app.include_router(auth_router, prefix="/api/v1")
app.include_router(contact_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, log_level="info")

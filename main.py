from ipaddress import ip_address
from typing import Callable

import cloudinary
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from slowapi.errors import RateLimitExceeded

from src.services import limiter
from src.api import contact_router, health_router, auth_router, user_router
from src.conf.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_API_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

origins = settings.ALLOWED_ORIGINS
banned_ips = settings.BANNED_IPS

app = FastAPI()
app.state.limiter = limiter
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def ban_ips_middleware(request: Request, call_next: Callable):
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
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Too many requests. Please try again later"},
    )


app.include_router(auth_router, prefix="/api/v1")
app.include_router(contact_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, log_level="info")

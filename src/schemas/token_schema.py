from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Defines the response structure for a successful user login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

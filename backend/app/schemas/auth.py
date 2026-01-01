"""Authentication schemas."""

from pydantic import BaseModel


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data."""

    username: str | None = None
    role: str

"""API models and schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# Health Check Models
class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Current environment")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# User Models
class UserBase(BaseModel):
    """Base user model."""

    email: EmailStr = Field(..., description="User email")
    username: str = Field(..., min_length=3, max_length=50, description="Username")


class UserCreate(UserBase):
    """User creation model."""

    password: str = Field(..., min_length=8, description="User password")


class UserUpdate(BaseModel):
    """User update model."""

    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)


class UserResponse(UserBase):
    """User response model."""

    id: int = Field(..., description="User ID")
    is_active: bool = Field(default=True, description="User active status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Auth Models
class Token(BaseModel):
    """Token response model."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenPayload(BaseModel):
    """Token payload."""

    sub: int = Field(..., description="User ID")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")


class LoginRequest(BaseModel):
    """Login request model."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


# API Response Models
class APIResponse(BaseModel):
    """Generic API response."""

    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    data: Optional[dict] = Field(None, description="Response data")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")


# Item Models (Example resource)
class ItemBase(BaseModel):
    """Base item model."""

    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(None, max_length=500, description="Item description")
    price: float = Field(..., gt=0, description="Item price")
    quantity: int = Field(default=0, ge=0, description="Item quantity")


class ItemCreate(ItemBase):
    """Item creation model."""

    pass


class ItemUpdate(BaseModel):
    """Item update model."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)


class ItemResponse(ItemBase):
    """Item response model."""

    id: int = Field(..., description="Item ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Pagination Models
class PaginatedResponse(BaseModel):
    """Paginated response model."""

    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")
    items: list = Field(default_factory=list, description="List of items")

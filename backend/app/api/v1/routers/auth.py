from fastapi import APIRouter, HTTPException
"""Authentication API endpoints."""

from datetime import timedelta
from app.core.security import create_access_token, verify_token
from app.core.config import settings
from app.schemas.auth import Token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint for authentication.

    Returns:
        Token: JWT access token
    """
    # This is a simplified implementation
    # In production, you would validate credentials against the database
    if form_data.username == "admin@doctorapp.com" and form_data.password == "admin123":
        access_token = create_access_token(data={"sub": form_data.username, "role": "admin"})
        return {"access_token": access_token, "token_type": "bearer"}
    elif form_data.username == "doctor@doctorapp.com" and form_data.password == "doctor123":
        access_token = create_access_token(data={"sub": form_data.username, "role": "doctor"})
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

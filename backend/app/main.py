"""
FastAPI application for Federated Health AI Platform.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, password, profile, patients

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Federated Health AI Platform - User Management API",
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address, enabled=settings.environment != "test")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(password.router)
app.include_router(patients.router)


@app.on_event("startup")
async def startup_db_client():
    """Initialize database connection on startup."""
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connection on shutdown."""
    await close_mongo_connection()


@app.get("/health")
def health_endpoint():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Federated Health AI Platform - User Management API",
        "version": settings.app_version,
        "docs": "/docs",
    }

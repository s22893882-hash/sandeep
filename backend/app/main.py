"""Main FastAPI application."""
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from app.api import auth, items, users
from app.config import get_settings
from app.logging import get_logger, setup_logging
from app.models import HealthResponse

# Setup logging
settings = get_settings()
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    # Startup
    logger.info(
        "Starting application",
        extra={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        },
    )

    yield

    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A modern FastAPI application with comprehensive logging and monitoring",
    docs_url=settings.docs_url if settings.docs_enabled else None,
    redoc_url=settings.redoc_url if settings.docs_enabled else None,
    lifespan=lifespan,
    debug=settings.debug,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Prometheus metrics endpoint (if not in development)
if not settings.is_development:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Include API routers
app.include_router(auth.router)
app.include_router(items.router)
app.include_router(users.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else None,
        },
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
        },
    )


@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Welcome to the API",
        "documentation": settings.docs_url,
        "version": settings.app_version,
    }


@app.get("/health", tags=["Health"], response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.utcnow(),
    )


@app.get("/config", tags=["System"])
async def get_config() -> dict:
    """Get public configuration."""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
        "docs_enabled": settings.docs_enabled,
    }


@app.middleware("http")
async def logging_middleware(request: Request, call_next) -> JSONResponse:
    """Log all incoming requests."""
    start_time = datetime.utcnow()

    logger.info(
        "Incoming request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
        },
    )

    response = await call_next(request)

    process_time = (datetime.utcnow() - start_time).total_seconds() * 1000

    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_ms": process_time,
        },
    )

    # Add timing header
    response.headers["X-Process-Time"] = str(process_time)

    return response

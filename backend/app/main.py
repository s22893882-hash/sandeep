"""
FastAPI application for doctor management system.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routers import doctors, auth, admin
from app.core.config import settings
from app.core.database import init_db

app = FastAPI(
    title="Doctor Management API",
    description="API for doctor profile management, verification, scheduling, and patient appointments",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(doctors.router, prefix="/api/doctors", tags=["Doctors"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.on_event("startup")
async def startup_event():
    """Initialize database and other services on startup."""
    await init_db()
    print("Doctor Management API started successfully")


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": app.version}


@app.get("/", tags=["System"])
async def root():
    """Root endpoint."""
    return {"message": "Doctor Management API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

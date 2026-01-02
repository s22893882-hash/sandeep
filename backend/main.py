"""
Federated Health AI Platform - Backend API
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import db, ensure_indexes
from app.routers import patients_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await db.connect()
    await ensure_indexes(db.get_db())
    yield
    # Shutdown
    await db.disconnect()


app = FastAPI(
    title="Federated Health AI Platform API",
    description="Backend API for the Federated Health AI Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Restricted CORS origins
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(patients_router)


@app.get("/health")
def health_endpoint():
    """FastAPI health endpoint."""
    return health_check()


def get_app_version():
    """Return the application version."""
    return "1.0.0"


def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": get_app_version(),
        "environment": "test",
    }


def calculate_sum(a: int, b: int) -> int:
    """Calculate sum of two numbers."""
    return a + b


def calculate_product(a: int, b: int) -> int:
    """Calculate product of two numbers."""
    return a * b


def validate_email(email: str) -> bool:
    """Validate email format."""
    return "@" in email and "." in email.split("@")[1]


class User:
    """User model."""

    def __init__(self, user_id: int, email: str, username: str):
        self.id = user_id
        self.email = email
        self.username = username
        self.is_active = True

    def to_dict(self):
        """Convert user to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "is_active": self.is_active,
        }

    def deactivate(self):
        """Deactivate the user."""
        self.is_active = False

    def activate(self):
        """Activate the user."""
        self.is_active = True

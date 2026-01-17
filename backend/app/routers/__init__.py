"""
API routers.
"""

from .auth import router as auth_router
from .profile import router as profile_router
from .password import router as password_router
from .patients import router as patients_router
from .consultations import router as consultations_router
from .payments import router as payments_router

# Export routers for easy inclusion in main app
router = [
    auth_router,
    profile_router,
    password_router,
    patients_router,
    consultations_router,
    payments_router,
]

__all__ = [
    "auth_router",
    "profile_router", 
    "password_router",
    "patients_router",
    "consultations_router",
    "payments_router",
]

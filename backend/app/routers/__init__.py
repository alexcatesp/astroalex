"""
API routers for Astroalex backend
"""
from .projects import router as projects_router
from .ingestion import router as ingestion_router
from .calibration import router as calibration_router

__all__ = [
    "projects_router",
    "ingestion_router",
    "calibration_router",
]

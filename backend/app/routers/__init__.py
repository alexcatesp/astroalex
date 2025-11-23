"""
API routers for Astroalex backend
"""
from .projects import router as projects_router
from .ingestion import router as ingestion_router
from .calibration import router as calibration_router
from .pipeline import router as pipeline_router
from .visualization import router as visualization_router
from .session import router as session_router
from .equipment import router as equipment_router
from .config import router as config_router

__all__ = [
    "session_router",
    "equipment_router",
    "config_router",
    "projects_router",
    "ingestion_router",
    "calibration_router",
    "pipeline_router",
    "visualization_router",
]

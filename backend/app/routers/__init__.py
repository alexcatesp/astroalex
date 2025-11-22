"""
API routers for Astroalex backend
"""
from .projects import router as projects_router
from .ingestion import router as ingestion_router
from .calibration import router as calibration_router
from .pipeline import router as pipeline_router
from .visualization import router as visualization_router

__all__ = [
    "projects_router",
    "ingestion_router",
    "calibration_router",
    "pipeline_router",
    "visualization_router",
]

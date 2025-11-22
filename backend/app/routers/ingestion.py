"""
File ingestion and organization API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
import logging

from app.models.metadata import FileMetadata
from app.services.project_service import ProjectService
from app.services.ingestion_service import IngestionService
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects/{project_id}/ingest", tags=["ingestion"])


def get_project_service() -> ProjectService:
    """Dependency to get ProjectService instance"""
    settings = get_settings()
    return ProjectService(settings.projects_base_dir)


def get_ingestion_service(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service)
) -> IngestionService:
    """Dependency to get IngestionService instance for a project"""
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return IngestionService(project.path)


@router.get("/scan", response_model=List[FileMetadata])
async def scan_ingest_directory(
    project_id: str,
    service: IngestionService = Depends(get_ingestion_service)
):
    """
    Scan the ingestion directory for FITS files.

    Returns metadata extracted from filenames for all discovered files.
    """
    try:
        files = service.scan_ingest_directory()
        return files
    except Exception as e:
        logger.error(f"Error scanning ingest directory: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats", response_model=dict)
async def get_ingest_stats(
    project_id: str,
    service: IngestionService = Depends(get_ingestion_service)
):
    """
    Get statistics about files in the ingestion directory.

    Returns counts by type, filter, object, and date.
    """
    try:
        stats = service.get_ingest_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting ingest stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/organize", response_model=dict)
async def organize_files(
    project_id: str,
    session_name: Optional[str] = None,
    copy: bool = False,
    service: IngestionService = Depends(get_ingestion_service)
):
    """
    Organize all files from ingestion directory to proper locations.

    Moves (or copies) files from 00_ingest/ to appropriate directories in
    01_raw_data/ based on their metadata.

    Args:
        project_id: Project identifier
        session_name: Optional calibration session name for calibration frames
        copy: If true, copy files instead of moving them
    """
    try:
        results = service.organize_all_files(session_name=session_name, copy=copy)
        return results
    except Exception as e:
        logger.error(f"Error organizing files: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

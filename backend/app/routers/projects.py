"""
Project management API endpoints
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
import logging

from app.models.project import Project, ProjectCreate, ProjectUpdate
from app.services.project_service import ProjectService
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_service() -> ProjectService:
    """Dependency to get ProjectService instance"""
    settings = get_settings()
    return ProjectService(settings.projects_base_dir)


@router.post("/", response_model=Project, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    service: ProjectService = Depends(get_project_service)
):
    """
    Create a new astrophotography project.

    Creates a project with the standard Astroalex directory structure.
    """
    try:
        project = service.create_project(project_data)
        return project
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[Project])
async def get_projects(service: ProjectService = Depends(get_project_service)):
    """
    Get all projects.

    Returns a list of all astrophotography projects.
    """
    try:
        projects = service.get_all_projects()
        return projects
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service)
):
    """
    Get a project by ID.

    Returns detailed information about a specific project.
    """
    try:
        project = service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    service: ProjectService = Depends(get_project_service)
):
    """
    Update a project.

    Updates project metadata (name, description).
    """
    try:
        project = service.update_project(project_id, project_data)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    delete_files: bool = False,
    service: ProjectService = Depends(get_project_service)
):
    """
    Delete a project.

    Args:
        project_id: Project identifier
        delete_files: If true, also delete project files from disk
    """
    try:
        success = service.delete_project(project_id, delete_files=delete_files)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{project_id}/validate", response_model=dict)
async def validate_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service)
):
    """
    Validate project directory structure.

    Checks that all required directories exist and are intact.
    """
    try:
        is_valid = service.validate_project(project_id)
        return {
            "project_id": project_id,
            "valid": is_valid,
            "message": "Project structure is valid" if is_valid else "Project structure is invalid"
        }
    except Exception as e:
        logger.error(f"Error validating project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

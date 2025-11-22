"""
Processing pipeline API endpoints
"""
from typing import List, Optional, Literal
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import logging

from app.models.pipeline import ProcessingPipeline
from app.services.project_service import ProjectService
from app.services.processing import PipelineService
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects/{project_id}/pipeline", tags=["pipeline"])


# Request models
class PipelineCreate(BaseModel):
    object_name: str
    filters: List[str]
    panels: Optional[List[str]] = None


class CalibrationRequest(BaseModel):
    science_paths: List[str]
    master_bias_path: Optional[str] = None
    master_dark_path: Optional[str] = None
    master_flat_path: Optional[str] = None


class QualityAnalysisRequest(BaseModel):
    file_paths: List[str]


class RegistrationRequest(BaseModel):
    source_paths: List[str]
    reference_path: Optional[str] = None


class StackingRequest(BaseModel):
    file_paths: List[str]
    method: Literal["median", "average", "sum"] = "median"
    rejection: Optional[Literal["sigma_clip", "minmax"]] = "sigma_clip"


def get_project_service() -> ProjectService:
    """Dependency to get ProjectService instance"""
    settings = get_settings()
    return ProjectService(settings.projects_base_dir)


def get_pipeline_service(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service)
) -> PipelineService:
    """Dependency to get PipelineService instance"""
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return PipelineService(project.path)


@router.post("/", response_model=ProcessingPipeline, status_code=201)
async def create_pipeline(
    project_id: str,
    pipeline_data: PipelineCreate,
    service: PipelineService = Depends(get_pipeline_service)
):
    """Create a new processing pipeline."""
    try:
        pipeline = service.create_pipeline(
            object_name=pipeline_data.object_name,
            filters=pipeline_data.filters,
            panels=pipeline_data.panels,
        )
        return pipeline
    except Exception as e:
        logger.error(f"Error creating pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ProcessingPipeline])
async def get_pipelines(
    project_id: str,
    service: PipelineService = Depends(get_pipeline_service)
):
    """Get all processing pipelines."""
    try:
        pipelines = service.get_pipelines()
        return pipelines
    except Exception as e:
        logger.error(f"Error getting pipelines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pipeline_id}/calibrate")
async def execute_calibration(
    project_id: str,
    pipeline_id: str,
    request: CalibrationRequest,
    service: PipelineService = Depends(get_pipeline_service)
):
    """Execute calibration step."""
    try:
        results = service.execute_calibration(
            pipeline_id=pipeline_id,
            science_paths=request.science_paths,
            master_bias_path=request.master_bias_path,
            master_dark_path=request.master_dark_path,
            master_flat_path=request.master_flat_path,
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing calibration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pipeline_id}/analyze")
async def execute_quality_analysis(
    project_id: str,
    pipeline_id: str,
    request: QualityAnalysisRequest,
    service: PipelineService = Depends(get_pipeline_service)
):
    """Execute quality analysis step."""
    try:
        results = service.execute_quality_analysis(
            pipeline_id=pipeline_id,
            file_paths=request.file_paths,
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing quality analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pipeline_id}/register")
async def execute_registration(
    project_id: str,
    pipeline_id: str,
    request: RegistrationRequest,
    service: PipelineService = Depends(get_pipeline_service)
):
    """Execute registration/alignment step."""
    try:
        results = service.execute_registration(
            pipeline_id=pipeline_id,
            source_paths=request.source_paths,
            reference_path=request.reference_path,
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing registration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pipeline_id}/stack")
async def execute_stacking(
    project_id: str,
    pipeline_id: str,
    request: StackingRequest,
    service: PipelineService = Depends(get_pipeline_service)
):
    """Execute stacking/integration step."""
    try:
        results = service.execute_stacking(
            pipeline_id=pipeline_id,
            file_paths=request.file_paths,
            method=request.method,
            rejection=request.rejection,
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing stacking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{pipeline_id}", status_code=204)
async def delete_pipeline(
    project_id: str,
    pipeline_id: str,
    service: PipelineService = Depends(get_pipeline_service)
):
    """Delete a processing pipeline."""
    try:
        success = service.delete_pipeline(pipeline_id)
        if not success:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

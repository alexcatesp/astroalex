"""
Calibration and master frame API endpoints
"""
from typing import List, Optional, Literal
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field
import logging

from app.models.metadata import CalibrationSession, MasterCalibration
from app.services.project_service import ProjectService
from app.services.calibration import MasterCalibrationService
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects/{project_id}/calibration", tags=["calibration"])


# Request/Response models
class SessionCreate(BaseModel):
    name: str = Field(..., description="Session name")
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    telescope: Optional[str] = None
    camera: Optional[str] = None


class MasterCreate(BaseModel):
    session_id: str = Field(..., description="Calibration session ID")
    frame_type: Literal["Bias", "Dark", "Flat"] = Field(..., description="Type of master frame")
    file_paths: List[str] = Field(..., description="Paths to frames to combine")
    method: Literal["average", "median"] = Field(default="median", description="Combination method")
    rejection: Optional[Literal["minmax", "sigma_clip"]] = Field(
        default="sigma_clip", description="Rejection method"
    )
    exposure_time: Optional[float] = None
    gain: Optional[int] = None
    filter_name: Optional[str] = Field(None, alias="filter")
    sigma_clip_low_thresh: float = 3.0
    sigma_clip_high_thresh: float = 3.0
    minmax_min: int = 1
    minmax_max: int = 1


def get_project_service() -> ProjectService:
    """Dependency to get ProjectService instance"""
    settings = get_settings()
    return ProjectService(settings.projects_base_dir)


def get_master_service(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service)
) -> MasterCalibrationService:
    """Dependency to get MasterCalibrationService instance"""
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return MasterCalibrationService(project.path)


@router.post("/sessions", response_model=CalibrationSession, status_code=201)
async def create_session(
    project_id: str,
    session_data: SessionCreate,
    service: MasterCalibrationService = Depends(get_master_service)
):
    """
    Create a new calibration session.
    """
    try:
        session = service.create_session(
            name=session_data.name,
            date=session_data.date,
            telescope=session_data.telescope,
            camera=session_data.camera
        )
        return session
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[CalibrationSession])
async def get_sessions(
    project_id: str,
    service: MasterCalibrationService = Depends(get_master_service)
):
    """
    Get all calibration sessions for a project.
    """
    try:
        sessions = service.get_sessions()
        return sessions
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=CalibrationSession)
async def get_session(
    project_id: str,
    session_id: str,
    service: MasterCalibrationService = Depends(get_master_service)
):
    """
    Get a calibration session by ID.
    """
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions/{session_name}/frames/{frame_type}")
async def scan_frames(
    project_id: str,
    session_name: str,
    frame_type: Literal["bias", "darks", "flats"],
    service: MasterCalibrationService = Depends(get_master_service)
):
    """
    Scan for calibration frames in a session directory.

    Returns information about each frame including statistics.
    """
    try:
        frames = service.scan_calibration_frames(session_name, frame_type)
        return {"session_name": session_name, "frame_type": frame_type, "frames": frames}
    except Exception as e:
        logger.error(f"Error scanning frames: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/masters", response_model=MasterCalibration, status_code=201)
async def create_master(
    project_id: str,
    master_data: MasterCreate,
    service: MasterCalibrationService = Depends(get_master_service)
):
    """
    Create a master calibration frame by combining multiple frames.

    This endpoint performs the actual frame combination using CCDProc.
    """
    try:
        master = service.create_master(
            session_id=master_data.session_id,
            frame_type=master_data.frame_type,
            file_paths=master_data.file_paths,
            method=master_data.method,
            rejection=master_data.rejection,
            exposure_time=master_data.exposure_time,
            gain=master_data.gain,
            filter_name=master_data.filter_name,
            sigma_clip_low_thresh=master_data.sigma_clip_low_thresh,
            sigma_clip_high_thresh=master_data.sigma_clip_high_thresh,
            minmax_min=master_data.minmax_min,
            minmax_max=master_data.minmax_max,
        )
        return master
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating master: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/masters", response_model=List[MasterCalibration])
async def get_masters(
    project_id: str,
    session_id: Optional[str] = None,
    service: MasterCalibrationService = Depends(get_master_service)
):
    """
    Get all master calibration frames.

    Optionally filter by session_id.
    """
    try:
        masters = service.get_masters(session_id=session_id)
        return masters
    except Exception as e:
        logger.error(f"Error getting masters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/masters/{master_id}", response_model=MasterCalibration)
async def get_master(
    project_id: str,
    master_id: str,
    service: MasterCalibrationService = Depends(get_master_service)
):
    """
    Get a master calibration frame by ID.
    """
    master = service.get_master(master_id)
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    return master


@router.delete("/masters/{master_id}", status_code=204)
async def delete_master(
    project_id: str,
    master_id: str,
    delete_file: bool = False,
    service: MasterCalibrationService = Depends(get_master_service)
):
    """
    Delete a master calibration frame.

    Args:
        master_id: Master frame ID
        delete_file: If true, also delete the FITS file from disk
    """
    try:
        success = service.delete_master(master_id, delete_file=delete_file)
        if not success:
            raise HTTPException(status_code=404, detail="Master not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting master: {e}")
        raise HTTPException(status_code=500, detail=str(e))

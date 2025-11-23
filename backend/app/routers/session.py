"""
API endpoints for observing session management
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from pathlib import Path
import shutil

from app.models.session import (
    ObservingSession,
    SessionCreate,
    SessionUpdate,
    SessionListItem,
    GeoLocation
)
from app.models.camera import CharacterizationInput
from app.services.session_service import SessionService
from app.services.environmental_service import EnvironmentalService
from app.services.camera_characterizer import CameraCharacterizer

router = APIRouter(prefix="/sessions", tags=["sessions"])

# Services
session_service = SessionService()
env_service = EnvironmentalService()
camera_service = CameraCharacterizer()


@router.post("/", response_model=ObservingSession)
def create_session(session_data: SessionCreate):
    """Create a new observing session"""
    session = session_service.create_session(session_data)
    return session


@router.get("/", response_model=List[SessionListItem])
def list_sessions():
    """List all observing sessions"""
    return session_service.list_sessions()


@router.get("/{session_id}", response_model=ObservingSession)
def get_session(session_id: str):
    """Get session by ID"""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/{session_id}", response_model=ObservingSession)
def update_session(session_id: str, update_data: SessionUpdate):
    """Update session data"""
    session = session_service.update_session(session_id, update_data)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}")
def delete_session(session_id: str):
    """Delete a session"""
    success = session_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted successfully"}


# STEP 1: Environmental Context
@router.post("/{session_id}/step1/context", response_model=ObservingSession)
def calculate_context(session_id: str, location: GeoLocation):
    """
    Step 1: Calculate environmental context

    - Calculate ephemeris (darkness window, moon phase)
    - Get sky conditions (placeholder for now)
    - Generate observing recommendations
    """
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Calculate ephemeris
    ephemeris = env_service.calculate_ephemeris(location)

    # Get sky conditions (placeholder)
    conditions = env_service.get_sky_conditions(location)

    # Generate recommendations
    recommendation_msg = env_service.generate_recommendations(conditions, ephemeris)

    # Update session
    update_data = SessionUpdate(
        location=location,
        conditions=conditions,
        ephemeris=ephemeris,
        status="step1_context"
    )
    session = session_service.update_session(session_id, update_data)

    # Add assistant message
    session = session_service.add_message(
        session_id,
        step="step1_context",
        message=recommendation_msg.message,
        data=recommendation_msg.data
    )

    return session


# STEP 2: Camera Characterization
@router.post("/{session_id}/step2/characterize")
async def characterize_camera(
    session_id: str,
    camera_model: str,
    gain_setting: int = None,
    bias1: UploadFile = File(...),
    bias2: UploadFile = File(...),
    flat1: UploadFile = File(...),
    flat2: UploadFile = File(...)
):
    """
    Step 2: Characterize camera sensor

    Upload 2 bias + 2 flat frames to calculate:
    - Read Noise (e-)
    - Gain (e-/ADU)
    - Full Well Capacity (e-)
    """
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Create temp directory for uploaded files
    temp_dir = Path("./data/temp") / session_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Save uploaded files
        bias1_path = temp_dir / "bias1.fits"
        bias2_path = temp_dir / "bias2.fits"
        flat1_path = temp_dir / "flat1.fits"
        flat2_path = temp_dir / "flat2.fits"

        with open(bias1_path, "wb") as f:
            shutil.copyfileobj(bias1.file, f)
        with open(bias2_path, "wb") as f:
            shutil.copyfileobj(bias2.file, f)
        with open(flat1_path, "wb") as f:
            shutil.copyfileobj(flat1.file, f)
        with open(flat2_path, "wb") as f:
            shutil.copyfileobj(flat2.file, f)

        # Characterize camera
        char_input = CharacterizationInput(
            bias_frames=[str(bias1_path), str(bias2_path)],
            flat_frames=[str(flat1_path), str(flat2_path)],
            camera_model=camera_model,
            gain_setting=gain_setting
        )

        result = camera_service.characterize(char_input)

        # Create sensor profile
        sensor_profile = camera_service.create_sensor_profile(
            result,
            camera_model=camera_model,
            gain_setting=gain_setting
        )

        # Update session
        update_data = SessionUpdate(
            camera_profile=sensor_profile,
            status="step2_camera"
        )
        session = session_service.update_session(session_id, update_data)

        # Generate message
        message = f"Perfil actualizado. Tu cámara está rindiendo a **{result.read_noise}e-** de ruido de lectura. "
        message += f"Gain: **{result.gain} e-/ADU**, Full Well: **{result.full_well_capacity:,} e-**. "
        message += "El sistema está calibrado."

        if result.warnings:
            message += f"\n\nAdvertencias: {'; '.join(result.warnings)}"

        session = session_service.add_message(
            session_id,
            step="step2_camera",
            message=message,
            data={
                "read_noise": result.read_noise,
                "gain": result.gain,
                "fwc": result.full_well_capacity,
                "confidence": result.confidence
            }
        )

        return session

    finally:
        # Cleanup temp files
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

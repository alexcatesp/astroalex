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
from app.services.target_selector import TargetSelector
from app.services.smart_scout import SmartScout
from app.services.flight_planner import FlightPlanGenerator

router = APIRouter(prefix="/sessions", tags=["sessions"])

# Services
session_service = SessionService()
env_service = EnvironmentalService()
camera_service = CameraCharacterizer()
target_service = TargetSelector()
scout_service = SmartScout()
planner_service = FlightPlanGenerator()


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
def calculate_context(session_id: str):
    """
    Step 1: Calculate environmental context

    - Calculate ephemeris (darkness window, moon phase)
    - Get sky conditions (from weather API)
    - Generate observing recommendations

    Uses the location from the session (set during creation)
    """
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.location:
        raise HTTPException(status_code=400, detail="Session must have a location set")

    # Calculate ephemeris
    ephemeris = env_service.calculate_ephemeris(session.location, session.date)

    # Get sky conditions
    conditions = env_service.get_sky_conditions(session.location)

    # Generate recommendations
    recommendation = env_service.generate_recommendations(conditions, ephemeris)

    # Update session
    update_data = SessionUpdate(
        conditions=conditions,
        ephemeris=ephemeris,
        status="step1_context"
    )
    session = session_service.update_session(session_id, update_data)

    # Add assistant message
    session = session_service.add_message(
        session_id,
        step="step1_context",
        message=recommendation.message,
        data=recommendation.data
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


# STEP 3: Target Selection
@router.post("/{session_id}/step3/suggest")
def suggest_targets(
    session_id: str,
    sensor_width: int = 3008,
    sensor_height: int = 3008,
    pixel_size: float = 3.76,
    focal_length: float = 600
):
    """
    Step 3: Get intelligent target suggestions

    Based on location, conditions, and equipment
    """
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.location or not session.ephemeris:
        raise HTTPException(status_code=400, detail="Complete Step 1 first (environmental context)")

    # Get suggestions
    suggestions = target_service.suggest_targets(
        location=session.location,
        ephemeris=session.ephemeris,
        sensor_width=sensor_width,
        sensor_height=sensor_height,
        pixel_size=pixel_size,
        focal_length=focal_length
    )

    # Format response
    results = [
        {
            "target": target.dict(),
            "score": metadata['total_score'],
            "visibility": metadata['visibility'],
            "fov_analysis": {
                "fov_width": metadata['fov_width'],
                "fov_height": metadata['fov_height'],
                "pixel_scale": metadata['pixel_scale']
            }
        }
        for target, metadata in suggestions
    ]

    return {"suggestions": results}


@router.post("/{session_id}/step3/select")
def select_target(
    session_id: str,
    target_name: str,
    sensor_width: int = 3008,
    sensor_height: int = 3008,
    pixel_size: float = 3.76,
    focal_length: float = 600
):
    """
    Step 3: Select and validate a target
    """
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Search for target
    matches = target_service.search_by_name(target_name)
    if not matches:
        raise HTTPException(status_code=404, detail=f"Target '{target_name}' not found")

    target = matches[0]

    # Validate target
    validation = target_service.validate_target(
        target=target,
        location=session.location,
        ephemeris=session.ephemeris,
        sensor_width=sensor_width,
        sensor_height=sensor_height,
        pixel_size=pixel_size,
        focal_length=focal_length
    )

    # Simulate FOV
    fov_sim = target_service.simulate_fov(
        target=target,
        sensor_width=sensor_width,
        sensor_height=sensor_height,
        pixel_size=pixel_size,
        focal_length=focal_length
    )

    # Update session
    update_data = SessionUpdate(
        target=target,
        fov_simulation=fov_sim,
        status="step3_target"
    )
    session = session_service.update_session(session_id, update_data)

    # Generate message
    message = f"Objetivo **{target.name}** ({target.catalog_id}) seleccionado.\n\n"
    message += "\n".join(f"• {rec}" for rec in validation['recommendations'])

    session = session_service.add_message(
        session_id,
        step="step3_target",
        message=message,
        data=validation
    )

    return session


# STEP 4: Smart Scout
@router.post("/{session_id}/step4/analyze")
async def analyze_scout_frame(
    session_id: str,
    exposure_time: float,
    filter_name: str = "L",
    test_frame: UploadFile = File(...)
):
    """
    Step 4: Analyze test frame for optimal exposure

    Upload a test frame to calculate:
    - Sky background
    - Saturation detection
    - Optimal exposure per filter
    - SNR estimate
    """
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.camera_profile:
        raise HTTPException(status_code=400, detail="Complete Step 2 first (camera characterization)")

    # Save test frame
    temp_dir = Path("./data/temp") / session_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        test_path = temp_dir / "test_frame.fits"
        with open(test_path, "wb") as f:
            shutil.copyfileobj(test_frame.file, f)

        # Analyze
        analysis = scout_service.analyze_test_frame(
            frame_path=str(test_path),
            sensor_profile=session.camera_profile,
            exposure_time=exposure_time,
            filter_name=filter_name
        )

        # Update session
        update_data = SessionUpdate(
            scout_analysis=analysis,
            status="step4_scout"
        )
        session = session_service.update_session(session_id, update_data)

        # Generate message
        message = scout_service.generate_recommendations(analysis, session.camera_profile)

        session = session_service.add_message(
            session_id,
            step="step4_scout",
            message=message,
            data=analysis.dict()
        )

        return session

    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


# STEP 5: Flight Plan
@router.post("/{session_id}/step5/generate")
def generate_flight_plan(
    session_id: str,
    available_hours: float = None
):
    """
    Step 5: Generate complete acquisition plan
    """
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.target or not session.scout_analysis:
        raise HTTPException(
            status_code=400,
            detail="Complete Steps 3 and 4 first (target selection and scout)"
        )

    # Generate plan
    plan = planner_service.generate_plan(
        target=session.target,
        ephemeris=session.ephemeris,
        scout_analysis=session.scout_analysis,
        available_hours=available_hours
    )

    # Update session
    update_data = SessionUpdate(
        acquisition_plan=plan,
        status="step5_plan"
    )
    session = session_service.update_session(session_id, update_data)

    # Generate message
    message = f"**Plan optimizado para {plan.target.name}:**\n\n"
    message += "**Luces:**\n"
    for filter_name, item in plan.lights.items():
        message += f"• {item.count} × {item.exposure}s ({filter_name})\n"

    message += f"\n**Calibración necesaria:**\n"
    for dark in plan.darks:
        message += f"• Darks: {dark.count} × {dark.exposure}s\n"
    message += f"• Flats: 20 por filtro\n"
    message += f"• Bias: {plan.bias.count}\n"

    message += f"\n**Tiempo total: {plan.total_time:.1f}h** ({plan.total_frames} frames)"

    if plan.hdr_strategy:
        message += f"\n\n⚠️ **Estrategia HDR activada**: combina exp. cortas ({plan.hdr_strategy['short_exposure']}s) y largas ({plan.hdr_strategy['long_exposure']}s)"

    session = session_service.add_message(
        session_id,
        step="step5_plan",
        message=message,
        data=plan.dict()
    )

    return session


@router.get("/{session_id}/step5/export/{format}")
def export_plan(session_id: str, format: str):
    """
    Step 5: Export plan to ASIAIR or NINA format

    Formats: 'asiair' or 'nina'
    """
    session = session_service.get_session(session_id)
    if not session or not session.acquisition_plan:
        raise HTTPException(status_code=404, detail="No plan found")

    output_dir = Path("./data/plans")
    output_dir.mkdir(parents=True, exist_ok=True)

    if format == "asiair":
        output_path = output_dir / f"{session_id}_asiair.plan"
        planner_service.export_asiair(session.acquisition_plan, str(output_path))
    elif format == "nina":
        output_path = output_dir / f"{session_id}_nina.json"
        planner_service.export_nina(session.acquisition_plan, str(output_path))
    else:
        raise HTTPException(status_code=400, detail="Format must be 'asiair' or 'nina'")

    from fastapi.responses import FileResponse
    return FileResponse(
        path=output_path,
        filename=output_path.name,
        media_type="application/json"
    )

"""
Data models for observing sessions and wizard workflow
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from enum import Enum
from .common import GeoLocation


class SessionStatus(str, Enum):
    """Status of an observing session"""
    CREATED = "created"
    STEP1_CONTEXT = "step1_context"
    STEP2_CAMERA = "step2_camera"
    STEP3_TARGET = "step3_target"
    STEP4_SCOUT = "step4_scout"
    STEP5_PLAN = "step5_plan"
    STEP6_INGESTION = "step6_ingestion"
    STEP7_QUALITY = "step7_quality"
    STEP8_PROCESSING = "step8_processing"
    COMPLETED = "completed"


class SkyConditions(BaseModel):
    """Current sky conditions from weather APIs"""
    seeing: float = Field(..., description="Seeing in arcseconds")
    clouds: int = Field(..., ge=0, le=100, description="Cloud coverage percentage")
    jet_stream: float = Field(..., description="Jet stream speed in m/s")
    transparency: Optional[int] = Field(None, ge=0, le=100, description="Atmospheric transparency percentage")
    humidity: Optional[int] = Field(None, ge=0, le=100, description="Humidity percentage")
    wind_speed: Optional[float] = Field(None, description="Wind speed in m/s")
    temperature: Optional[float] = Field(None, description="Temperature in Celsius")
    source: str = Field(..., description="Data source (Meteoblue, OpenMeteo, etc.)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Ephemeris(BaseModel):
    """Astronomical ephemeris data"""
    darkness_start: datetime = Field(..., description="Start of astronomical darkness")
    darkness_end: datetime = Field(..., description="End of astronomical darkness")
    darkness_duration: float = Field(..., description="Duration of darkness in hours")
    moon_phase: float = Field(..., ge=0, le=1, description="Moon phase (0=new, 1=full)")
    moon_illumination: int = Field(..., ge=0, le=100, description="Moon illumination percentage")
    moon_alt: Optional[float] = Field(None, description="Moon altitude in degrees")
    sun_set: datetime = Field(..., description="Sunset time")
    sun_rise: datetime = Field(..., description="Sunrise time")
    astronomical_twilight_start: datetime = Field(..., description="Evening astronomical twilight")
    astronomical_twilight_end: datetime = Field(..., description="Morning astronomical twilight")


class SensorProfile(BaseModel):
    """Camera sensor characterization profile"""
    camera_model: str = Field(..., description="Camera model name")
    read_noise: float = Field(..., description="Read noise in electrons (e-)")
    gain: float = Field(..., description="Gain in e-/ADU")
    full_well_capacity: int = Field(..., description="Full well capacity in electrons")
    measured_date: datetime = Field(default_factory=datetime.utcnow)
    temperature: Optional[float] = Field(None, description="Sensor temperature in Celsius")
    gain_setting: Optional[int] = Field(None, description="Gain setting used")
    offset: Optional[int] = Field(None, description="Offset setting")
    binning: Optional[str] = Field(None, description="Binning mode (e.g., '1x1', '2x2')")
    notes: Optional[str] = None


class CelestialTarget(BaseModel):
    """Celestial object target"""
    name: str = Field(..., description="Common name")
    catalog_id: str = Field(..., description="Catalog identifier (NGC, IC, M, etc.)")
    ra: float = Field(..., ge=0, lt=360, description="Right ascension in degrees")
    dec: float = Field(..., ge=-90, le=90, description="Declination in degrees")
    size: float = Field(..., description="Angular size in arcminutes")
    surface_brightness: Optional[float] = Field(None, description="Surface brightness in mag/arcsec²")
    optimal_filters: List[str] = Field(default_factory=list, description="Recommended filters")
    object_type: Optional[str] = Field(None, description="Type (galaxy, nebula, cluster, etc.)")
    constellation: Optional[str] = None
    magnitude: Optional[float] = None


class FOVSimulation(BaseModel):
    """Field of view simulation result"""
    target: str
    fits_in_frame: bool
    coverage_percentage: float = Field(..., ge=0, le=100)
    pixel_scale: float = Field(..., description="Arcsec/pixel")
    fov_width: float = Field(..., description="FOV width in arcminutes")
    fov_height: float = Field(..., description="FOV height in arcminutes")
    target_size: float = Field(..., description="Target size in arcminutes")
    rotation_needed: Optional[float] = Field(None, description="Recommended rotation in degrees")


class ScoutAnalysis(BaseModel):
    """Smart Scout analysis results"""
    sky_background: float = Field(..., description="Sky background in electrons/second")
    saturation_detected: bool
    saturation_percentage: float = Field(..., ge=0, le=100)
    saturated_pixels: int
    hdr_required: bool
    optimal_exposure: Dict[str, int] = Field(..., description="Optimal exposure per filter in seconds")
    snr_estimate: float = Field(..., description="Signal-to-noise ratio estimate")
    fwhm: Optional[float] = Field(None, description="FWHM in arcseconds")
    star_count: Optional[int] = Field(None, description="Detected stars")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)


class PlanItem(BaseModel):
    """Single item in acquisition plan"""
    frame_type: str = Field(..., description="Type: light, dark, flat, bias")
    filter_name: Optional[str] = None
    exposure: int = Field(..., description="Exposure time in seconds")
    gain: Optional[int] = None
    count: int = Field(..., description="Number of frames")
    total_time: float = Field(..., description="Total time in minutes")


class AcquisitionPlan(BaseModel):
    """Complete acquisition plan for the session"""
    target: CelestialTarget
    lights: Dict[str, PlanItem] = Field(..., description="Light frames by filter")
    darks: List[PlanItem]
    flats: List[PlanItem]
    bias: PlanItem
    total_time: float = Field(..., description="Total acquisition time in hours")
    total_frames: int
    hdr_strategy: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AssistantMessage(BaseModel):
    """Message from the assistant to the user"""
    step: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Optional[Dict[str, Any]] = None


class ObservingSession(BaseModel):
    """Complete observing session with all wizard steps"""
    id: str = Field(..., description="Unique session ID")
    name: str = Field(..., description="Session name")
    date: datetime = Field(default_factory=datetime.utcnow)
    status: SessionStatus = Field(default=SessionStatus.CREATED)

    # Equipment profile reference
    equipment_profile_id: Optional[str] = Field(None, description="Reference to equipment profile used")

    # Location and conditions (Step 1)
    location: Optional[GeoLocation] = None
    conditions: Optional[SkyConditions] = None
    ephemeris: Optional[Ephemeris] = None

    # Camera characterization (Step 2)
    camera_profile: Optional[SensorProfile] = None

    # Target selection (Step 3)
    target: Optional[CelestialTarget] = None
    fov_simulation: Optional[FOVSimulation] = None

    # Smart Scout (Step 4)
    scout_analysis: Optional[ScoutAnalysis] = None

    # Flight Plan (Step 5)
    acquisition_plan: Optional[AcquisitionPlan] = None

    # Associated project (Step 6+)
    project_id: Optional[str] = None
    project_path: Optional[str] = None

    # Assistant conversation history
    messages: List[AssistantMessage] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class SessionCreate(BaseModel):
    """Request to create a new session"""
    name: str = Field(..., min_length=1, max_length=200)
    date: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Date of observing session")
    location: Optional[GeoLocation] = None
    equipment_profile_id: Optional[str] = None


class SessionUpdate(BaseModel):
    """Request to update session data"""
    name: Optional[str] = None
    status: Optional[SessionStatus] = None
    location: Optional[GeoLocation] = None
    conditions: Optional[SkyConditions] = None
    ephemeris: Optional[Ephemeris] = None
    camera_profile: Optional[SensorProfile] = None
    target: Optional[CelestialTarget] = None
    fov_simulation: Optional[FOVSimulation] = None
    scout_analysis: Optional[ScoutAnalysis] = None
    acquisition_plan: Optional[AcquisitionPlan] = None
    project_id: Optional[str] = None


class SessionListItem(BaseModel):
    """Minimal session info for listing"""
    id: str
    name: str
    date: datetime
    status: SessionStatus
    target_name: Optional[str] = None
    location_name: Optional[str] = None
    created_at: datetime

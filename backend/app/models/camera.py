"""
Data models for camera characterization
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class BiasFrame(BaseModel):
    """Bias frame for characterization"""
    file_path: str
    mean: float
    median: float
    std: float
    min_val: float
    max_val: float


class FlatFrame(BaseModel):
    """Flat frame for characterization"""
    file_path: str
    mean_level: float
    median_level: float
    std: float
    exposure: Optional[float] = None


class CharacterizationInput(BaseModel):
    """Input data for camera characterization"""
    bias_frames: List[str] = Field(..., min_length=2, description="Paths to bias frames")
    flat_frames: List[str] = Field(..., min_length=2, description="Paths to flat frames")
    camera_model: Optional[str] = None
    gain_setting: Optional[int] = None
    offset: Optional[int] = None
    temperature: Optional[float] = None


class CharacterizationResult(BaseModel):
    """Results from camera characterization"""
    read_noise: float = Field(..., description="Read noise in electrons")
    gain: float = Field(..., description="Gain in e-/ADU")
    full_well_capacity: int = Field(..., description="Full well capacity in electrons")

    # Detailed stats
    bias_stats: dict = Field(..., description="Bias frames statistics")
    flat_stats: dict = Field(..., description="Flat frames statistics")

    # Quality metrics
    confidence: float = Field(..., ge=0, le=1, description="Measurement confidence")
    warnings: List[str] = Field(default_factory=list)

    measured_at: datetime = Field(default_factory=datetime.utcnow)


class KnownCamera(BaseModel):
    """Pre-populated camera specifications"""
    manufacturer: str
    model: str
    sensor: str
    read_noise_spec: float = Field(..., description="Manufacturer spec read noise (e-)")
    gain_spec: float = Field(..., description="Manufacturer spec gain (e-/ADU)")
    full_well_spec: int = Field(..., description="Manufacturer spec FWC (e-)")
    pixel_size: float = Field(..., description="Pixel size in micrometers")
    resolution: str = Field(..., description="Resolution (e.g., '3008x3008')")
    notes: Optional[str] = None

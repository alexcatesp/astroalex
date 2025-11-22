"""
Metadata models for FITS files and calibration
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class FileMetadata(BaseModel):
    """Metadata extracted from FITS filenames and headers"""
    filename: str = Field(..., description="Original filename")
    image_type: Literal["Light", "Dark", "Bias", "Flat"] = Field(..., description="Type of image")
    object_name: Optional[str] = Field(None, description="Astronomical object name")
    filter: Optional[str] = Field(None, description="Filter used (L, R, G, B, Ha, SII, OIII, etc.)")
    exposure_time: Optional[float] = Field(None, description="Exposure time in seconds")
    gain: Optional[int] = Field(None, description="Camera gain setting")
    date: Optional[str] = Field(None, description="Observation date (YYYY-MM-DD)")
    sequence: Optional[str] = Field(None, description="Sequence number")

    # Additional FITS header metadata
    temperature: Optional[float] = Field(None, description="Sensor temperature in Celsius")
    binning: Optional[str] = Field(None, description="Binning mode (e.g., '1x1', '2x2')")
    instrument: Optional[str] = Field(None, description="Camera/instrument name")

    class Config:
        from_attributes = True


class CalibrationSession(BaseModel):
    """Calibration session grouping darks, flats, and bias frames"""
    id: str = Field(..., description="Unique session identifier")
    name: str = Field(..., description="Session name (e.g., '2025-10-26_Newton200_ASI533')")
    date: str = Field(..., description="Session date (YYYY-MM-DD)")
    telescope: Optional[str] = Field(None, description="Telescope used")
    camera: Optional[str] = Field(None, description="Camera used")
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class MasterCalibration(BaseModel):
    """Master calibration frame (combined Dark, Flat, or Bias)"""
    id: str = Field(..., description="Unique master frame identifier")
    session_id: str = Field(..., description="Associated calibration session")
    type: Literal["Bias", "Dark", "Flat"] = Field(..., description="Type of master frame")
    exposure_time: Optional[float] = Field(None, description="Exposure time (for darks/flats)")
    gain: Optional[int] = Field(None, description="Gain setting")
    filter: Optional[str] = Field(None, description="Filter (for flats)")
    filename: str = Field(..., description="Master frame filename")
    num_frames: int = Field(..., description="Number of frames combined")
    combination_method: str = Field(default="median", description="Combination method used")
    rejection_method: Optional[str] = Field(None, description="Rejection method used")
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True

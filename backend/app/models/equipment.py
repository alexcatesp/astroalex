"""
Equipment Profile Models
Models for camera, telescope, mount, filters and complete equipment profiles
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .common import GeoLocation


class CameraInfo(BaseModel):
    """Camera information and specifications"""
    model: str = Field(..., description="Camera model name (e.g., 'ZWO ASI294MC Pro')")
    manufacturer: str = Field(default="", description="Camera manufacturer")
    sensor_width: int = Field(..., description="Sensor width in pixels", gt=0)
    sensor_height: int = Field(..., description="Sensor height in pixels", gt=0)
    pixel_size: float = Field(..., description="Pixel size in microns", gt=0)

    # Optional: Characterized values (from Step 2)
    read_noise: Optional[float] = Field(None, description="Measured read noise in electrons")
    gain: Optional[float] = Field(None, description="Measured gain in e-/ADU")
    full_well_capacity: Optional[int] = Field(None, description="Full well capacity in electrons")

    # Additional specs
    color: bool = Field(default=True, description="Color (OSC) or monochrome sensor")
    cooling: bool = Field(default=False, description="Has active cooling")
    bit_depth: int = Field(default=16, description="ADC bit depth")


class TelescopeInfo(BaseModel):
    """Telescope/lens information"""
    name: str = Field(..., description="Telescope/lens name")
    manufacturer: str = Field(default="", description="Manufacturer")
    focal_length: int = Field(..., description="Focal length in mm", gt=0)
    aperture: int = Field(..., description="Aperture diameter in mm", gt=0)
    focal_ratio: Optional[float] = Field(None, description="f-ratio (calculated if not provided)")
    telescope_type: str = Field(
        default="refractor",
        description="Type: refractor, reflector, SCT, MCT, etc."
    )

    def __init__(self, **data):
        super().__init__(**data)
        # Auto-calculate focal ratio if not provided
        if self.focal_ratio is None and self.aperture > 0:
            self.focal_ratio = round(self.focal_length / self.aperture, 1)


class MountInfo(BaseModel):
    """Mount information"""
    name: str = Field(..., description="Mount name")
    manufacturer: str = Field(default="", description="Manufacturer")
    mount_type: str = Field(
        default="eq",
        description="Mount type: eq (equatorial), altaz, dobsonian"
    )
    goto_capable: bool = Field(default=True, description="Has GoTo capability")
    payload_capacity: Optional[float] = Field(None, description="Max payload in kg")


class FilterInfo(BaseModel):
    """Filter information"""
    name: str = Field(..., description="Filter name (e.g., 'L', 'Ha', 'R', 'G', 'B')")
    type: str = Field(
        ...,
        description="Filter type: broadband, narrowband, LRGB, RGB, SHO"
    )
    bandwidth: Optional[int] = Field(None, description="Filter bandwidth in nm")
    central_wavelength: Optional[int] = Field(None, description="Central wavelength in nm")

    # Common filter presets
    @staticmethod
    def luminance():
        return FilterInfo(name="L", type="LRGB", bandwidth=None)

    @staticmethod
    def red():
        return FilterInfo(name="R", type="RGB", central_wavelength=630)

    @staticmethod
    def green():
        return FilterInfo(name="G", type="RGB", central_wavelength=530)

    @staticmethod
    def blue():
        return FilterInfo(name="B", type="RGB", central_wavelength=470)

    @staticmethod
    def h_alpha():
        return FilterInfo(name="Ha", type="narrowband", bandwidth=7, central_wavelength=656)

    @staticmethod
    def oiii():
        return FilterInfo(name="OIII", type="narrowband", bandwidth=8, central_wavelength=500)

    @staticmethod
    def sii():
        return FilterInfo(name="SII", type="narrowband", bandwidth=8, central_wavelength=672)


class EquipmentProfile(BaseModel):
    """Complete equipment profile"""
    id: str = Field(..., description="Unique profile ID")
    name: str = Field(..., description="Profile name (e.g., 'Mi setup principal')")
    description: Optional[str] = Field(None, description="Profile description")

    # Equipment components
    camera: CameraInfo
    telescope: TelescopeInfo
    mount: Optional[MountInfo] = None
    filters: List[FilterInfo] = Field(default_factory=list, description="Available filters")

    # Default location for this setup
    default_location: Optional[GeoLocation] = None

    # Metadata
    is_active: bool = Field(default=False, description="Currently active profile")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Calculated properties
    @property
    def fov_width(self) -> float:
        """Calculate FOV width in degrees"""
        sensor_width_mm = self.camera.sensor_width * self.camera.pixel_size / 1000
        return 2 * (180 / 3.14159) * (sensor_width_mm / (2 * self.telescope.focal_length))

    @property
    def fov_height(self) -> float:
        """Calculate FOV height in degrees"""
        sensor_height_mm = self.camera.sensor_height * self.camera.pixel_size / 1000
        return 2 * (180 / 3.14159) * (sensor_height_mm / (2 * self.telescope.focal_length))

    @property
    def pixel_scale(self) -> float:
        """Calculate pixel scale in arcseconds/pixel"""
        return 206.265 * self.camera.pixel_size / self.telescope.focal_length

    @property
    def sampling_quality(self) -> str:
        """Assess sampling quality based on pixel scale"""
        # Assuming typical seeing of 2-3 arcsec
        if self.pixel_scale < 0.5:
            return "oversampled"
        elif self.pixel_scale <= 1.5:
            return "optimal"
        elif self.pixel_scale <= 3.0:
            return "acceptable"
        else:
            return "undersampled"


class EquipmentCreate(BaseModel):
    """Request model for creating equipment profile"""
    name: str
    description: Optional[str] = None
    camera: CameraInfo
    telescope: TelescopeInfo
    mount: Optional[MountInfo] = None
    filters: List[FilterInfo] = Field(default_factory=list)
    default_location: Optional[GeoLocation] = None


class EquipmentUpdate(BaseModel):
    """Request model for updating equipment profile"""
    name: Optional[str] = None
    description: Optional[str] = None
    camera: Optional[CameraInfo] = None
    telescope: Optional[TelescopeInfo] = None
    mount: Optional[MountInfo] = None
    filters: Optional[List[FilterInfo]] = None
    default_location: Optional[GeoLocation] = None
    is_active: Optional[bool] = None

"""
Configuration Models
Storage configuration and user state management
"""
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
from .common import GeoLocation


class StorageConfig(BaseModel):
    """Storage paths configuration"""
    raw_data_path: str = Field(
        ...,
        description="Path for raw FITS files (can be external drive)"
    )
    processed_data_path: str = Field(
        ...,
        description="Path for processed data output"
    )
    projects_path: str = Field(
        ...,
        description="Path for project metadata and structure"
    )
    cache_path: str = Field(
        default="./data/cache",
        description="Path for temporary cache files"
    )

    def validate_paths(self) -> dict:
        """Validate that all paths exist or can be created"""
        results = {}
        for field_name in ["raw_data_path", "processed_data_path", "projects_path", "cache_path"]:
            path = Path(getattr(self, field_name))
            try:
                path.mkdir(parents=True, exist_ok=True)
                results[field_name] = {"valid": True, "exists": path.exists()}
            except Exception as e:
                results[field_name] = {"valid": False, "error": str(e)}
        return results


class UserState(BaseModel):
    """User onboarding and preferences state"""
    # Onboarding flags
    first_time: bool = Field(default=True, description="First time using the app")
    has_equipment_profile: bool = Field(
        default=False,
        description="Has created at least one equipment profile"
    )
    has_characterized_camera: bool = Field(
        default=False,
        description="Has characterized camera sensor"
    )
    onboarding_completed: bool = Field(
        default=False,
        description="Has completed initial onboarding"
    )

    # Active settings
    active_equipment_profile_id: Optional[str] = Field(
        None,
        description="Currently active equipment profile ID"
    )
    last_location: Optional[GeoLocation] = Field(
        None,
        description="Last used observation location"
    )

    # User preferences
    preferred_units: str = Field(
        default="metric",
        description="Preferred unit system: metric or imperial"
    )
    language: str = Field(default="es", description="UI language")
    theme: str = Field(default="dark", description="UI theme: dark or light")

    # Storage configuration
    storage_configured: bool = Field(
        default=False,
        description="Has configured storage paths"
    )
    storage_config: Optional[StorageConfig] = None


class AppConfig(BaseModel):
    """Complete application configuration"""
    user_state: UserState = Field(default_factory=UserState)
    storage: Optional[StorageConfig] = None

    # API keys (for future external integrations)
    meteoblue_api_key: Optional[str] = None
    astrometry_api_key: Optional[str] = None

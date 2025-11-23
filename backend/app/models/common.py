"""
Common data models shared across the application
"""
from pydantic import BaseModel, Field
from typing import Optional


class GeoLocation(BaseModel):
    """Geographic location"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    elevation: Optional[float] = Field(None, description="Elevation in meters")
    timezone: str = Field(..., description="Timezone (e.g., 'America/New_York')")
    name: Optional[str] = Field(None, description="Location name")

"""
Data models for environmental context and astronomical calculations
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class WeatherForecast(BaseModel):
    """Extended weather forecast"""
    date: datetime
    seeing_forecast: Optional[float] = None
    cloud_forecast: Optional[int] = None
    transparency_forecast: Optional[int] = None
    temperature_forecast: Optional[float] = None


class AstronomicalNight(BaseModel):
    """Complete astronomical night information"""
    date: datetime
    sunset: datetime
    sunrise: datetime
    civil_twilight_evening: datetime
    civil_twilight_morning: datetime
    nautical_twilight_evening: datetime
    nautical_twilight_morning: datetime
    astronomical_twilight_evening: datetime
    astronomical_twilight_morning: datetime
    darkness_duration_hours: float
    moon_phase: float
    moon_illumination: int
    moon_rise: Optional[datetime] = None
    moon_set: Optional[datetime] = None


class ObservingRecommendation(BaseModel):
    """AI-generated observing recommendations"""
    overall_quality: str = Field(..., description="excellent, good, mediocre, poor")
    seeing_recommendation: str
    filter_recommendation: List[str]
    binning_recommendation: Optional[str] = None
    notes: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0, le=1, description="Recommendation confidence")


class ContextSummary(BaseModel):
    """Complete environmental context summary"""
    location: str
    date: datetime
    sky_conditions: Any  # SkyConditions from session.py
    ephemeris: Any  # Ephemeris from session.py
    recommendation: ObservingRecommendation
    generated_at: datetime = Field(default_factory=datetime.utcnow)

"""
Processing pipeline models
"""
from datetime import datetime
from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field


class ProcessingStep(BaseModel):
    """Individual step in the processing pipeline"""
    type: Literal["calibration", "quality_analysis", "registration", "stacking"] = Field(
        ..., description="Type of processing step"
    )
    config: Dict[str, Any] = Field(default_factory=dict, description="Step configuration parameters")
    status: Literal["pending", "running", "completed", "failed"] = Field(
        default="pending", description="Step execution status"
    )
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")
    error_message: Optional[str] = Field(None, description="Error message if step failed")

    class Config:
        from_attributes = True


class ProcessingPipeline(BaseModel):
    """Complete processing pipeline for an object"""
    id: str = Field(..., description="Unique pipeline identifier")
    project_id: str = Field(..., description="Associated project ID")
    object_name: str = Field(..., description="Astronomical object being processed")
    filters: List[str] = Field(default_factory=list, description="Filters to process")
    panels: Optional[List[str]] = Field(None, description="Mosaic panel names (if applicable)")
    steps: List[ProcessingStep] = Field(default_factory=list, description="Processing steps")
    status: Literal["pending", "running", "completed", "failed"] = Field(
        default="pending", description="Overall pipeline status"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True

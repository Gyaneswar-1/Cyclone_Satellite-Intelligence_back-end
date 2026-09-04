from typing import List, Optional
from pydantic import BaseModel, Field


class AIAnalysisRequest(BaseModel):
    """Request payload for multimodal AI cyclone analysis."""
    storm_id: str = Field(..., json_schema_extra={"example": "storm-001"})
    timestamp: str = Field(..., json_schema_extra={"example": "2026-09-04T18:00:00Z"})
    image_url: Optional[str] = Field(None, json_schema_extra={"example": "http://server/image.jpg"})
    wind_kts: Optional[float] = Field(None, json_schema_extra={"example": 72.0})
    pressure_hpa: Optional[float] = Field(None, json_schema_extra={"example": 982.0})
    previous_timestamp: Optional[str] = Field(None, json_schema_extra={"example": "2026-09-04T15:00:00Z"})
    previous_wind_kts: Optional[float] = Field(None, json_schema_extra={"example": 68.0})
    previous_pressure_hpa: Optional[float] = Field(None, json_schema_extra={"example": 985.0})
    satellites: List[str] = Field(default_factory=list, json_schema_extra={"example": ["Meteosat-5", "GMS-5"]})


class ModelComponentOutput(BaseModel):
    """Schema for individual AI/rule component predictions with experimental markers."""
    label: str
    confidence: Optional[float] = None
    method: str
    experimental: bool = True


class AnalysisEvidence(BaseModel):
    """Evidence metrics supporting AI inference."""
    wind_kts: Optional[float] = None
    pressure_hpa: Optional[float] = None
    wind_delta_kts: Optional[float] = None
    pressure_delta_hpa: Optional[float] = None
    satellites: List[str] = Field(default_factory=list)


class AIAnalysisResponse(BaseModel):
    """Full normalized AI response structure."""
    storm_id: str
    timestamp: str
    pattern: ModelComponentOutput
    strength_trend: ModelComponentOutput
    next_stage: ModelComponentOutput
    evidence: AnalysisEvidence
    warnings: List[str] = Field(
        default_factory=lambda: [
            "Prototype research output; not an official IMD forecast."
        ]
    )

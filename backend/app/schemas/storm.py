from typing import List, Optional
from pydantic import BaseModel, Field


class StormObservation(BaseModel):
    """Normalized observation schema representing a single temporal satellite snapshot."""
    storm_id: str = Field(..., description="Unique cyclone identifier")
    storm_name: str = Field(..., description="Official or catalog cyclone name")
    timestamp: str = Field(..., description="ISO 8601 observation timestamp")
    lat: Optional[float] = Field(None, description="Center latitude coordinate")
    lon: Optional[float] = Field(None, description="Center longitude coordinate")
    wind_kts: Optional[float] = Field(None, description="Maximum sustained wind speed in knots")
    pressure_hpa: Optional[float] = Field(None, description="Central pressure in hPa")
    image_url: Optional[str] = Field(None, description="URL or local path to satellite image")
    satellites: List[str] = Field(default_factory=list, description="Satellites observing this timestamp")
    stage: Optional[str] = Field(None, description="Prototype lifecycle stage label")


class StormTrackPoint(BaseModel):
    """Single spatial-temporal point along cyclone track."""
    timestamp: str
    lat: float
    lon: float
    wind_kts: Optional[float] = None
    pressure_hpa: Optional[float] = None
    stage: Optional[str] = None


class StormTrack(BaseModel):
    """Complete cyclone spatial track for MapLibre map rendering."""
    storm_id: str
    storm_name: str
    track: List[StormTrackPoint]


class StormDetail(BaseModel):
    """Summary details for active cyclone list."""
    storm_id: str
    storm_name: str
    active: bool = True
    start_time: str
    latest_time: str
    max_wind_kts: float = 0.0
    min_pressure_hpa: float = 1010.0
    observation_count: int = 0
    latest_observation: Optional[StormObservation] = None

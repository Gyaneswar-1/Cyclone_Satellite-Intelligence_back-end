from typing import List, Optional
from pydantic import BaseModel, Field


class SatelliteObservation(BaseModel):
    """Metadata for a satellite imagery capture."""
    storm_id: str
    timestamp: str
    satellite: str
    image_url: str
    channel: str = "IR"
    resolution_km: Optional[float] = 4.0


class SatelliteTimeline(BaseModel):
    """Chronological list of satellite observations for a cyclone."""
    storm_id: str
    total_images: int
    observations: List[SatelliteObservation]

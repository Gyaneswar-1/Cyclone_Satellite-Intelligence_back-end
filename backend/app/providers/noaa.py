from typing import List, Optional

from backend.app.providers.base import BaseStormProvider
from backend.app.providers.mock import MockProvider
from backend.app.schemas.storm import StormDetail, StormObservation, StormTrack
from backend.app.schemas.satellite import SatelliteTimeline


class NOAAProvider(BaseStormProvider):
    """NOAA / HURSAT Satellite Data Provider Adapter with Mock Fallback."""

    def __init__(self, base_url: str = "https://www.ncei.noaa.gov/data/hurricane-satellite-hursat-b1/archive/v06"):
        self.base_url = base_url.rstrip("/")
        self.fallback_provider = MockProvider()

    async def get_active_storms(self) -> List[StormDetail]:
        return await self.fallback_provider.get_active_storms()

    async def get_storm_detail(self, storm_id: str) -> Optional[StormDetail]:
        return await self.fallback_provider.get_storm_detail(storm_id)

    async def get_observations(self, storm_id: str) -> List[StormObservation]:
        return await self.fallback_provider.get_observations(storm_id)

    async def get_track(self, storm_id: str) -> Optional[StormTrack]:
        return await self.fallback_provider.get_track(storm_id)

    async def get_satellite_timeline(self, storm_id: str) -> Optional[SatelliteTimeline]:
        return await self.fallback_provider.get_satellite_timeline(storm_id)

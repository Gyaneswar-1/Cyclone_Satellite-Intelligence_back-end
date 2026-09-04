from typing import List, Optional
import httpx

from backend.app.providers.base import BaseStormProvider
from backend.app.providers.mock import MockProvider
from backend.app.schemas.storm import StormDetail, StormObservation, StormTrack
from backend.app.schemas.satellite import SatelliteTimeline
from backend.app.utils.logging import logger


class IMDProvider(BaseStormProvider):
    """India Meteorological Department (IMD) Live Data Provider Adapter with Mock Fallback."""

    def __init__(self, base_url: str = "https://api.imd.gov.in"):
        self.base_url = base_url.rstrip("/")
        self.fallback_provider = MockProvider()

    async def get_active_storms(self) -> List[StormDetail]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/cyclone/active")
                if resp.status_code == 200:
                    data = resp.json()
                    # Example normalization if IMD API responds
                    return [
                        StormDetail(
                            storm_id=str(item.get("id")),
                            storm_name=str(item.get("name")),
                            active=True,
                            start_time=str(item.get("start_time")),
                            latest_time=str(item.get("latest_time")),
                            max_wind_kts=float(item.get("max_wind", 0)),
                            min_pressure_hpa=float(item.get("min_pressure", 1010)),
                            observation_count=int(item.get("obs_count", 1))
                        )
                        for item in data
                    ]
        except Exception as e:
            logger.warning(f"[IMDProvider] Connection error or endpoint unavailable ({e}). Falling back to MockProvider.")

        return await self.fallback_provider.get_active_storms()

    async def get_storm_detail(self, storm_id: str) -> Optional[StormDetail]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/cyclone/{storm_id}")
                if resp.status_code == 200:
                    item = resp.json()
                    return StormDetail(
                        storm_id=str(item.get("id", storm_id)),
                        storm_name=str(item.get("name", "IMD Storm")),
                        active=True,
                        start_time=str(item.get("start_time")),
                        latest_time=str(item.get("latest_time")),
                        max_wind_kts=float(item.get("max_wind", 0)),
                        min_pressure_hpa=float(item.get("min_pressure", 1010)),
                        observation_count=int(item.get("obs_count", 1))
                    )
        except Exception as e:
            logger.warning(f"[IMDProvider] Error fetching storm detail for {storm_id}: {e}")

        return await self.fallback_provider.get_storm_detail(storm_id)

    async def get_observations(self, storm_id: str) -> List[StormObservation]:
        return await self.fallback_provider.get_observations(storm_id)

    async def get_track(self, storm_id: str) -> Optional[StormTrack]:
        return await self.fallback_provider.get_track(storm_id)

    async def get_satellite_timeline(self, storm_id: str) -> Optional[SatelliteTimeline]:
        return await self.fallback_provider.get_satellite_timeline(storm_id)

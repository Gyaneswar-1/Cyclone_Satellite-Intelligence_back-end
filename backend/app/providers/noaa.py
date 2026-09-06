from typing import List, Optional
import httpx

from backend.app.providers.base import BaseStormProvider
from backend.app.providers.mock import MockProvider
from backend.app.schemas.storm import StormDetail, StormObservation, StormTrack, StormTrackPoint
from backend.app.schemas.satellite import SatelliteObservation, SatelliteTimeline
from backend.app.utils.logging import logger
from backend.app.utils.time import format_iso_utc


class NOAAProvider(BaseStormProvider):
    """NOAA / HURSAT Satellite Data Provider Adapter with Mock Fallback."""

    def __init__(self, base_url: str = "https://www.ncei.noaa.gov/data/hurricane-satellite-hursat-b1/archive/v06"):
        self.base_url = base_url.rstrip("/")
        self.fallback_provider = MockProvider()

    async def get_active_storms(self) -> List[StormDetail]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/storms")
                if resp.status_code == 200:
                    data = resp.json()
                    storms = [
                        StormDetail(
                            storm_id=str(item.get("storm_id", item.get("id"))),
                            storm_name=str(item.get("storm_name", item.get("name", "NOAA Storm"))),
                            active=bool(item.get("active", True)),
                            start_time=format_iso_utc(item.get("start_time", "")),
                            latest_time=format_iso_utc(item.get("latest_time", "")),
                            max_wind_kts=float(item.get("max_wind_kts", item.get("max_wind", 0))),
                            min_pressure_hpa=float(item.get("min_pressure_hpa", item.get("min_pressure", 1010))),
                            observation_count=int(item.get("observation_count", item.get("obs_count", 1))),
                        )
                        for item in data
                    ]
                    if storms:
                        return storms
        except Exception as e:
            logger.warning(f"[NOAAProvider] Live archive API unavailable ({e}). Falling back to MockProvider.")

        return await self.fallback_provider.get_active_storms()

    async def get_storm_detail(self, storm_id: str) -> Optional[StormDetail]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/{storm_id}/summary")
                if resp.status_code == 200:
                    item = resp.json()
                    return StormDetail(
                        storm_id=str(item.get("storm_id", storm_id)),
                        storm_name=str(item.get("storm_name", "NOAA Storm")),
                        active=bool(item.get("active", True)),
                        start_time=format_iso_utc(item.get("start_time", "")),
                        latest_time=format_iso_utc(item.get("latest_time", "")),
                        max_wind_kts=float(item.get("max_wind_kts", item.get("max_wind", 0))),
                        min_pressure_hpa=float(item.get("min_pressure_hpa", item.get("min_pressure", 1010))),
                        observation_count=int(item.get("observation_count", 1)),
                    )
        except Exception as e:
            logger.warning(f"[NOAAProvider] Error fetching storm detail for {storm_id} ({e}). Falling back to MockProvider.")

        return await self.fallback_provider.get_storm_detail(storm_id)

    async def get_observations(self, storm_id: str) -> List[StormObservation]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/{storm_id}/observations")
                if resp.status_code == 200:
                    data = resp.json()
                    obs = [
                        StormObservation(
                            storm_id=str(item.get("storm_id", storm_id)),
                            storm_name=str(item.get("storm_name", "NOAA Storm")),
                            timestamp=format_iso_utc(item.get("timestamp", "")),
                            lat=float(item.get("lat")) if item.get("lat") is not None else None,
                            lon=float(item.get("lon")) if item.get("lon") is not None else None,
                            wind_kts=float(item.get("wind_kts")) if item.get("wind_kts") is not None else None,
                            pressure_hpa=float(item.get("pressure_hpa")) if item.get("pressure_hpa") is not None else None,
                            image_url=item.get("image_url"),
                            satellites=item.get("satellites", ["HURSAT-B1", "GOES"]),
                            stage=item.get("stage", "organizing"),
                        )
                        for item in data
                    ]
                    if obs:
                        return obs
        except Exception as e:
            logger.warning(f"[NOAAProvider] Error fetching observations for {storm_id} ({e}). Falling back to MockProvider.")

        return await self.fallback_provider.get_observations(storm_id)

    async def get_track(self, storm_id: str) -> Optional[StormTrack]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/{storm_id}/track")
                if resp.status_code == 200:
                    data = resp.json()
                    pts = [
                        StormTrackPoint(
                            timestamp=format_iso_utc(p.get("timestamp", "")),
                            lat=float(p["lat"]),
                            lon=float(p["lon"]),
                            wind_kts=float(p.get("wind_kts")) if p.get("wind_kts") is not None else None,
                            pressure_hpa=float(p.get("pressure_hpa")) if p.get("pressure_hpa") is not None else None,
                            stage=p.get("stage"),
                        )
                        for p in data.get("track", [])
                        if "lat" in p and "lon" in p
                    ]
                    return StormTrack(
                        storm_id=str(data.get("storm_id", storm_id)),
                        storm_name=str(data.get("storm_name", "NOAA Storm")),
                        track=pts,
                    )
        except Exception as e:
            logger.warning(f"[NOAAProvider] Error fetching track for {storm_id} ({e}). Falling back to MockProvider.")

        return await self.fallback_provider.get_track(storm_id)

    async def get_satellite_timeline(self, storm_id: str) -> Optional[SatelliteTimeline]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/{storm_id}/satellite")
                if resp.status_code == 200:
                    data = resp.json()
                    observations = [
                        SatelliteObservation(
                            storm_id=str(item.get("storm_id", storm_id)),
                            timestamp=format_iso_utc(item.get("timestamp", "")),
                            satellite=str(item.get("satellite", "HURSAT-B1")),
                            image_url=str(item.get("image_url", "")),
                            channel=str(item.get("channel", "IR")),
                            resolution_km=float(item.get("resolution_km", 4.0)),
                        )
                        for item in data.get("observations", [])
                    ]
                    return SatelliteTimeline(
                        storm_id=str(data.get("storm_id", storm_id)),
                        total_images=int(data.get("total_images", len(observations))),
                        observations=observations,
                    )
        except Exception as e:
            logger.warning(f"[NOAAProvider] Error fetching satellite timeline for {storm_id} ({e}). Falling back to MockProvider.")

        return await self.fallback_provider.get_satellite_timeline(storm_id)

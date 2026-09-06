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
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/cyclone/{storm_id}/observations")
                if resp.status_code == 200:
                    data = resp.json()
                    observations = []
                    for item in data:
                        raw_ts = str(item.get("timestamp", ""))
                        observations.append(
                            StormObservation(
                                storm_id=str(item.get("storm_id", storm_id)),
                                storm_name=str(item.get("storm_name", "IMD Storm")),
                                timestamp=format_iso_utc(raw_ts),
                                lat=float(item.get("lat")) if item.get("lat") is not None else None,
                                lon=float(item.get("lon")) if item.get("lon") is not None else None,
                                wind_kts=float(item.get("wind_kts")) if item.get("wind_kts") is not None else None,
                                pressure_hpa=float(item.get("pressure_hpa")) if item.get("pressure_hpa") is not None else None,
                                image_url=item.get("image_url"),
                                satellites=item.get("satellites", ["INSAT-3D"]),
                                stage=item.get("stage", "organizing"),
                            )
                        )
                    if observations:
                        return observations
        except Exception as e:
            logger.warning(f"[IMDProvider] Error fetching observations for {storm_id} ({e}). Falling back to MockProvider.")

        return await self.fallback_provider.get_observations(storm_id)

    async def get_track(self, storm_id: str) -> Optional[StormTrack]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/cyclone/{storm_id}/track")
                if resp.status_code == 200:
                    data = resp.json()
                    track_pts = [
                        StormTrackPoint(
                            timestamp=format_iso_utc(pt.get("timestamp", "")),
                            lat=float(pt["lat"]),
                            lon=float(pt["lon"]),
                            wind_kts=float(pt.get("wind_kts")) if pt.get("wind_kts") is not None else None,
                            pressure_hpa=float(pt.get("pressure_hpa")) if pt.get("pressure_hpa") is not None else None,
                            stage=pt.get("stage"),
                        )
                        for pt in data.get("track", [])
                        if "lat" in pt and "lon" in pt
                    ]
                    return StormTrack(
                        storm_id=str(data.get("storm_id", storm_id)),
                        storm_name=str(data.get("storm_name", "IMD Storm")),
                        track=track_pts,
                    )
        except Exception as e:
            logger.warning(f"[IMDProvider] Error fetching track for {storm_id} ({e}). Falling back to MockProvider.")

        return await self.fallback_provider.get_track(storm_id)

    async def get_satellite_timeline(self, storm_id: str) -> Optional[SatelliteTimeline]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/cyclone/{storm_id}/satellite")
                if resp.status_code == 200:
                    data = resp.json()
                    observations = [
                        SatelliteObservation(
                            storm_id=str(obs.get("storm_id", storm_id)),
                            timestamp=format_iso_utc(obs.get("timestamp", "")),
                            satellite=str(obs.get("satellite", "INSAT-3D")),
                            image_url=str(obs.get("image_url", "")),
                            channel=str(obs.get("channel", "IR")),
                            resolution_km=float(obs.get("resolution_km", 4.0)),
                        )
                        for obs in data.get("observations", [])
                    ]
                    return SatelliteTimeline(
                        storm_id=str(data.get("storm_id", storm_id)),
                        total_images=int(data.get("total_images", len(observations))),
                        observations=observations,
                    )
        except Exception as e:
            logger.warning(f"[IMDProvider] Error fetching satellite timeline for {storm_id} ({e}). Falling back to MockProvider.")

        return await self.fallback_provider.get_satellite_timeline(storm_id)

from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

from backend.app.providers.base import BaseStormProvider
from backend.app.schemas.storm import StormDetail, StormObservation, StormTrack, StormTrackPoint
from backend.app.schemas.satellite import SatelliteObservation, SatelliteTimeline
from backend.app.utils.logging import logger

DATA_PATH = Path("stormsense_dataset/processed/clean_observations_v2.csv")


class MockProvider(BaseStormProvider):
    """Mock Provider supplying dataset observations or synthetic fallback cyclone tracks."""

    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
        self._load_data()

    def _load_data(self):
        if DATA_PATH.exists():
            try:
                self._df = pd.read_csv(DATA_PATH)
                logger.info(f"[MockProvider] Loaded {len(self._df)} clean observations from {DATA_PATH}")
            except Exception as e:
                logger.warning(f"[MockProvider] Failed to read dataset from {DATA_PATH}: {e}")
                self._df = None
        else:
            logger.info(f"[MockProvider] Dataset file {DATA_PATH} not found; using fallback mock storms.")

    async def get_active_storms(self) -> List[StormDetail]:
        if self._df is not None and not self._df.empty:
            storm_groups = self._df.groupby("storm_id")
            storms = []
            for storm_id, group in storm_groups:
                name = str(group["storm_name"].iloc[0])
                sorted_group = group.sort_values("timestamp")
                start_time = str(sorted_group["timestamp"].iloc[0])
                latest_time = str(sorted_group["timestamp"].iloc[-1])
                max_wind = float(group["wind_kts"].max()) if "wind_kts" in group and not group["wind_kts"].isna().all() else 0.0
                min_press = float(group["pressure_hpa"].min()) if "pressure_hpa" in group and not group["pressure_hpa"].isna().all() else 1010.0
                latest_row = sorted_group.iloc[-1]
                latest_obs = StormObservation(
                    storm_id=str(storm_id),
                    storm_name=name,
                    timestamp=str(latest_row["timestamp"]),
                    lat=float(latest_row["lat"]) if pd.notna(latest_row.get("lat")) else None,
                    lon=float(latest_row["lon"]) if pd.notna(latest_row.get("lon")) else None,
                    wind_kts=float(latest_row["wind_kts"]) if pd.notna(latest_row.get("wind_kts")) else None,
                    pressure_hpa=float(latest_row["pressure_hpa"]) if pd.notna(latest_row.get("pressure_hpa")) else None,
                    image_url=str(latest_row.get("image_path", "")) if pd.notna(latest_row.get("image_path")) else None,
                    satellites=[str(latest_row.get("satellites", "Meteosat-5"))],
                    stage=str(latest_row.get("stage", "organizing"))
                )
                storms.append(StormDetail(
                    storm_id=str(storm_id),
                    storm_name=name,
                    active=True,
                    start_time=start_time,
                    latest_time=latest_time,
                    max_wind_kts=max_wind,
                    min_pressure_hpa=min_press,
                    observation_count=len(group),
                    latest_observation=latest_obs
                ))
            return storms[:10]

        # Synthetic fallback cyclone if CSV not present
        return [
            StormDetail(
                storm_id="storm-001",
                storm_name="FANI",
                active=True,
                start_time="2026-09-04T00:00:00Z",
                latest_time="2026-09-04T18:00:00Z",
                max_wind_kts=90.0,
                min_pressure_hpa=960.0,
                observation_count=4,
                latest_observation=StormObservation(
                    storm_id="storm-001",
                    storm_name="FANI",
                    timestamp="2026-09-04T18:00:00Z",
                    lat=18.42,
                    lon=85.13,
                    wind_kts=90.0,
                    pressure_hpa=960.0,
                    image_url="http://localhost:8000/static/sample.jpg",
                    satellites=["INSAT-3D", "Meteosat-5"],
                    stage="mature"
                )
            )
        ]

    async def get_storm_detail(self, storm_id: str) -> Optional[StormDetail]:
        storms = await self.get_active_storms()
        for s in storms:
            if s.storm_id == storm_id:
                return s
        return storms[0] if storms else None

    async def get_observations(self, storm_id: str) -> List[StormObservation]:
        if self._df is not None and not self._df.empty:
            sub = self._df[self._df["storm_id"].astype(str) == str(storm_id)].sort_values("timestamp")
            if sub.empty:
                sub = self._df.head(10)
            observations = []
            for _, row in sub.iterrows():
                observations.append(StormObservation(
                    storm_id=str(row.get("storm_id", storm_id)),
                    storm_name=str(row.get("storm_name", "UNKNOWN")),
                    timestamp=str(row.get("timestamp", "")),
                    lat=float(row["lat"]) if pd.notna(row.get("lat")) else None,
                    lon=float(row["lon"]) if pd.notna(row.get("lon")) else None,
                    wind_kts=float(row["wind_kts"]) if pd.notna(row.get("wind_kts")) else None,
                    pressure_hpa=float(row["pressure_hpa"]) if pd.notna(row.get("pressure_hpa")) else None,
                    image_url=str(row.get("image_path", "")) if pd.notna(row.get("image_path")) else None,
                    satellites=[str(row.get("satellites", "Meteosat-5"))],
                    stage=str(row.get("stage", "organizing"))
                ))
            return observations

        # Fallback synthetic observations
        return [
            StormObservation(storm_id=storm_id, storm_name="FANI", timestamp="2026-09-04T06:00:00Z", lat=16.5, lon=84.1, wind_kts=65.0, pressure_hpa=985.0, satellites=["INSAT-3D"], stage="organizing"),
            StormObservation(storm_id=storm_id, storm_name="FANI", timestamp="2026-09-04T12:00:00Z", lat=17.4, lon=84.6, wind_kts=78.0, pressure_hpa=972.0, satellites=["INSAT-3D"], stage="organizing"),
            StormObservation(storm_id=storm_id, storm_name="FANI", timestamp="2026-09-04T18:00:00Z", lat=18.42, lon=85.13, wind_kts=90.0, pressure_hpa=960.0, satellites=["INSAT-3D"], stage="mature"),
        ]

    async def get_track(self, storm_id: str) -> Optional[StormTrack]:
        obs = await self.get_observations(storm_id)
        if not obs:
            return None
        points = [
            StormTrackPoint(
                timestamp=o.timestamp,
                lat=o.lat if o.lat is not None else 0.0,
                lon=o.lon if o.lon is not None else 0.0,
                wind_kts=o.wind_kts,
                pressure_hpa=o.pressure_hpa,
                stage=o.stage
            )
            for o in obs if o.lat is not None and o.lon is not None
        ]
        return StormTrack(
            storm_id=storm_id,
            storm_name=obs[0].storm_name if obs else "UNKNOWN",
            track=points
        )

    async def get_satellite_timeline(self, storm_id: str) -> Optional[SatelliteTimeline]:
        obs = await self.get_observations(storm_id)
        sat_obs = [
            SatelliteObservation(
                storm_id=storm_id,
                timestamp=o.timestamp,
                satellite=o.satellites[0] if o.satellites else "Meteosat-5",
                image_url=o.image_url or "http://localhost:8000/static/sample.jpg",
                channel="IR"
            )
            for o in obs
        ]
        return SatelliteTimeline(
            storm_id=storm_id,
            total_images=len(sat_obs),
            observations=sat_obs
        )

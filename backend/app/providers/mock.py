from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

from backend.app.providers.base import BaseStormProvider
from backend.app.schemas.storm import StormDetail, StormObservation, StormTrack, StormTrackPoint
from backend.app.schemas.satellite import SatelliteObservation, SatelliteTimeline
from backend.app.utils.logging import logger
from backend.app.utils.time import format_iso_utc

DATA_PATH = Path("stormsense_dataset/processed/clean_observations_v2.csv")


def _parse_satellites(val) -> List[str]:
    """Parse comma-separated satellite names or single satellite value."""
    if pd.isna(val) or val is None or not str(val).strip():
        return ["Meteosat-5"]
    if isinstance(val, list):
        return [str(s).strip() for s in val if str(s).strip()]
    return [s.strip() for s in str(val).split(",") if s.strip()]


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

    def _build_storm_observation(self, row) -> StormObservation:
        storm_id = str(row.get("storm_id", ""))
        storm_name = str(row.get("storm_name", "UNKNOWN"))
        raw_ts = str(row.get("timestamp", ""))
        timestamp = format_iso_utc(raw_ts)

        lat = float(row["lat"]) if pd.notna(row.get("lat")) else None
        lon = float(row["lon"]) if pd.notna(row.get("lon")) else None
        wind_kts = float(row["wind_kts"]) if pd.notna(row.get("wind_kts")) else None
        pressure_hpa = float(row["pressure_hpa"]) if pd.notna(row.get("pressure_hpa")) else None
        image_url = str(row.get("image_path", "")) if pd.notna(row.get("image_path")) else None
        satellites = _parse_satellites(row.get("satellites"))
        stage = str(row.get("stage", "organizing")) if pd.notna(row.get("stage")) else "organizing"

        return StormObservation(
            storm_id=storm_id,
            storm_name=storm_name,
            timestamp=timestamp,
            lat=lat,
            lon=lon,
            wind_kts=wind_kts,
            pressure_hpa=pressure_hpa,
            image_url=image_url,
            satellites=satellites,
            stage=stage,
        )

    def _build_storm_detail(self, storm_id: str, group: pd.DataFrame) -> StormDetail:
        name = str(group["storm_name"].iloc[0])
        sorted_group = group.sort_values("timestamp")
        start_time = format_iso_utc(str(sorted_group["timestamp"].iloc[0]))
        latest_time = format_iso_utc(str(sorted_group["timestamp"].iloc[-1]))
        max_wind = (
            float(group["wind_kts"].max())
            if "wind_kts" in group and not group["wind_kts"].isna().all()
            else 0.0
        )
        min_press = (
            float(group["pressure_hpa"].min())
            if "pressure_hpa" in group and not group["pressure_hpa"].isna().all()
            else 1010.0
        )
        latest_row = sorted_group.iloc[-1]
        latest_obs = self._build_storm_observation(latest_row)

        return StormDetail(
            storm_id=str(storm_id),
            storm_name=name,
            active=True,
            start_time=start_time,
            latest_time=latest_time,
            max_wind_kts=max_wind,
            min_pressure_hpa=min_press,
            observation_count=len(group),
            latest_observation=latest_obs,
        )

    def _get_synthetic_fani_detail(self) -> StormDetail:
        latest_obs = StormObservation(
            storm_id="storm-001",
            storm_name="FANI",
            timestamp="2026-09-04T18:00:00Z",
            lat=18.42,
            lon=85.13,
            wind_kts=90.0,
            pressure_hpa=960.0,
            image_url="http://localhost:8000/static/sample.jpg",
            satellites=["INSAT-3D", "Meteosat-5"],
            stage="mature",
        )
        return StormDetail(
            storm_id="storm-001",
            storm_name="FANI",
            active=True,
            start_time="2026-09-04T00:00:00Z",
            latest_time="2026-09-04T18:00:00Z",
            max_wind_kts=90.0,
            min_pressure_hpa=960.0,
            observation_count=4,
            latest_observation=latest_obs,
        )

    def _get_synthetic_fani_observations(self) -> List[StormObservation]:
        return [
            StormObservation(
                storm_id="storm-001",
                storm_name="FANI",
                timestamp="2026-09-04T00:00:00Z",
                lat=15.8,
                lon=83.5,
                wind_kts=55.0,
                pressure_hpa=992.0,
                image_url="http://localhost:8000/static/sample.jpg",
                satellites=["INSAT-3D", "Meteosat-5"],
                stage="developing",
            ),
            StormObservation(
                storm_id="storm-001",
                storm_name="FANI",
                timestamp="2026-09-04T06:00:00Z",
                lat=16.5,
                lon=84.1,
                wind_kts=65.0,
                pressure_hpa=985.0,
                image_url="http://localhost:8000/static/sample.jpg",
                satellites=["INSAT-3D", "Meteosat-5"],
                stage="organizing",
            ),
            StormObservation(
                storm_id="storm-001",
                storm_name="FANI",
                timestamp="2026-09-04T12:00:00Z",
                lat=17.4,
                lon=84.6,
                wind_kts=78.0,
                pressure_hpa=972.0,
                image_url="http://localhost:8000/static/sample.jpg",
                satellites=["INSAT-3D", "Meteosat-5"],
                stage="organizing",
            ),
            StormObservation(
                storm_id="storm-001",
                storm_name="FANI",
                timestamp="2026-09-04T18:00:00Z",
                lat=18.42,
                lon=85.13,
                wind_kts=90.0,
                pressure_hpa=960.0,
                image_url="http://localhost:8000/static/sample.jpg",
                satellites=["INSAT-3D", "Meteosat-5"],
                stage="mature",
            ),
        ]

    async def get_active_storms(self) -> List[StormDetail]:
        storms = []
        has_fani = False

        if self._df is not None and not self._df.empty:
            storm_groups = self._df.groupby("storm_id")
            for storm_id, group in storm_groups:
                if str(storm_id) == "storm-001":
                    has_fani = True
                storms.append(self._build_storm_detail(str(storm_id), group))

        # Always include synthetic FANI if not present in dataset
        if not has_fani:
            storms.insert(0, self._get_synthetic_fani_detail())

        return storms

    async def get_storm_detail(self, storm_id: str) -> Optional[StormDetail]:
        if self._df is not None and not self._df.empty:
            sub = self._df[self._df["storm_id"].astype(str) == str(storm_id)]
            if not sub.empty:
                return self._build_storm_detail(str(storm_id), sub)

        if str(storm_id) == "storm-001":
            return self._get_synthetic_fani_detail()

        return None

    async def get_observations(self, storm_id: str) -> List[StormObservation]:
        if self._df is not None and not self._df.empty:
            sub = self._df[self._df["storm_id"].astype(str) == str(storm_id)].sort_values("timestamp")
            if not sub.empty:
                return [self._build_storm_observation(row) for _, row in sub.iterrows()]

        if str(storm_id) == "storm-001":
            return self._get_synthetic_fani_observations()

        return []

    async def get_track(self, storm_id: str) -> Optional[StormTrack]:
        obs = await self.get_observations(storm_id)
        if not obs:
            return None

        points = [
            StormTrackPoint(
                timestamp=o.timestamp,
                lat=o.lat,
                lon=o.lon,
                wind_kts=o.wind_kts,
                pressure_hpa=o.pressure_hpa,
                stage=o.stage,
            )
            for o in obs
            if o.lat is not None and o.lon is not None
        ]

        return StormTrack(
            storm_id=storm_id,
            storm_name=obs[0].storm_name if obs else "UNKNOWN",
            track=points,
        )

    async def get_satellite_timeline(self, storm_id: str) -> Optional[SatelliteTimeline]:
        obs = await self.get_observations(storm_id)
        if not obs:
            return None

        sat_obs = [
            SatelliteObservation(
                storm_id=storm_id,
                timestamp=o.timestamp,
                satellite=o.satellites[0] if o.satellites else "Meteosat-5",
                image_url=o.image_url or "http://localhost:8000/static/sample.jpg",
                channel="IR",
                resolution_km=4.0,
            )
            for o in obs
        ]

        return SatelliteTimeline(
            storm_id=storm_id,
            total_images=len(sat_obs),
            observations=sat_obs,
        )

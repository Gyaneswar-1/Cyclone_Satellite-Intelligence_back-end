from abc import ABC, abstractmethod
from typing import List, Optional
from backend.app.schemas.storm import StormDetail, StormObservation, StormTrack
from backend.app.schemas.satellite import SatelliteTimeline


class BaseStormProvider(ABC):
    """Abstract Base Class for Cyclone Data Providers."""

    @abstractmethod
    async def get_active_storms(self) -> List[StormDetail]:
        """Fetch list of currently active or available cyclone details."""
        pass

    @abstractmethod
    async def get_storm_detail(self, storm_id: str) -> Optional[StormDetail]:
        """Fetch summary detail for a specific cyclone."""
        pass

    @abstractmethod
    async def get_observations(self, storm_id: str) -> List[StormObservation]:
        """Fetch ordered historical observations for a cyclone."""
        pass

    @abstractmethod
    async def get_track(self, storm_id: str) -> Optional[StormTrack]:
        """Fetch spatial-temporal track points for MapLibre map rendering."""
        pass

    @abstractmethod
    async def get_satellite_timeline(self, storm_id: str) -> Optional[SatelliteTimeline]:
        """Fetch satellite observations timeline for a cyclone."""
        pass

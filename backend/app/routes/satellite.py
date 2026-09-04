from fastapi import APIRouter, HTTPException, Path

from backend.app.providers import get_provider
from backend.app.schemas.satellite import SatelliteObservation, SatelliteTimeline

router = APIRouter(prefix="/api/storms/{storm_id}/satellite", tags=["Satellite"])


@router.get("", response_model=SatelliteTimeline, summary="Get Satellite Imagery Timeline")
async def get_satellite_timeline(storm_id: str = Path(..., description="Unique cyclone identifier")):
    """Returns chronological satellite observations and imagery for a cyclone."""
    provider = get_provider()
    timeline = await provider.get_satellite_timeline(storm_id)
    if not timeline:
        raise HTTPException(status_code=404, detail=f"Satellite timeline not found for cyclone '{storm_id}'.")
    return timeline


@router.get("/latest", response_model=SatelliteObservation, summary="Get Latest Satellite Imagery Metadata")
async def get_latest_satellite(storm_id: str = Path(..., description="Unique cyclone identifier")):
    """Returns metadata for the most recent satellite observation."""
    provider = get_provider()
    timeline = await provider.get_satellite_timeline(storm_id)
    if not timeline or not timeline.observations:
        raise HTTPException(status_code=404, detail=f"No satellite observations found for cyclone '{storm_id}'.")
    return timeline.observations[-1]


@router.get("/timeline", response_model=SatelliteTimeline, summary="Get Satellite Observations List")
async def get_satellite_observations(storm_id: str = Path(..., description="Unique cyclone identifier")):
    """Returns satellite observation list for timeline UI rendering."""
    provider = get_provider()
    timeline = await provider.get_satellite_timeline(storm_id)
    if not timeline:
        raise HTTPException(status_code=404, detail=f"Satellite timeline not found for cyclone '{storm_id}'.")
    return timeline

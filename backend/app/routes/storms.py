from typing import List
from fastapi import APIRouter, HTTPException, Path

from backend.app.providers import get_provider
from backend.app.schemas.storm import StormDetail, StormObservation, StormTrack

router = APIRouter(prefix="/api/storms", tags=["Storms"])


@router.get("", response_model=List[StormDetail], summary="Get Active / Available Cyclones")
async def get_active_storms():
    """Returns list of active or available cyclone details."""
    provider = get_provider()
    return await provider.get_active_storms()


@router.get("/{storm_id}", response_model=StormDetail, summary="Get Cyclone Detail")
async def get_storm_detail(storm_id: str = Path(..., description="Unique cyclone identifier")):
    """Returns summary detail for a specific cyclone."""
    provider = get_provider()
    detail = await provider.get_storm_detail(storm_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Cyclone '{storm_id}' not found.")
    return detail


@router.get("/{storm_id}/observations", response_model=List[StormObservation], summary="Get Cyclone Observations")
async def get_storm_observations(storm_id: str = Path(..., description="Unique cyclone identifier")):
    """Returns chronological observations for a cyclone."""
    provider = get_provider()
    obs = await provider.get_observations(storm_id)
    if not obs:
        raise HTTPException(status_code=404, detail=f"No observations found for cyclone '{storm_id}'.")
    return obs


@router.get("/{storm_id}/track", response_model=StormTrack, summary="Get Cyclone Spatial Track")
async def get_storm_track(storm_id: str = Path(..., description="Unique cyclone identifier")):
    """Returns coordinates and intensity track suitable for MapLibre map integration."""
    provider = get_provider()
    track = await provider.get_track(storm_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"Track data not found for cyclone '{storm_id}'.")
    return track

"""FastAPI router for external integrations: YouTube, Leaflet Maps, and PM Accelerator."""

from typing import Optional
from fastapi import APIRouter, Query
from backend.services.integrations import (
    get_youtube_travel_videos,
    get_map_metadata,
    PM_ACCELERATOR_DETAILS,
)

router = APIRouter(prefix="/api/integrations", tags=["Integrations"])


@router.get("/youtube")
def get_travel_videos(
    location: str = Query(..., min_length=1, description="Location name for tour/travel videos"),
    max_results: int = Query(4, ge=1, le=10),
):
    """Retrieves relevant YouTube tour videos or provides genuine search fallback URL."""
    return get_youtube_travel_videos(location, max_results=max_results)


@router.get("/map")
def get_map_config(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    name: Optional[str] = Query("Selected Location"),
):
    """Provides OpenStreetMap tile configuration and pin coordinates for Leaflet."""
    return get_map_metadata(lat, lon, name)


@router.get("/pm-accelerator")
def get_organization_info():
    """Returns official PM Accelerator mission, program details, and developer credits."""
    return PM_ACCELERATOR_DETAILS

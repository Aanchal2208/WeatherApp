"""FastAPI router for location geocoding services."""

from fastapi import APIRouter, HTTPException, Query, status
from backend.schemas import LocationGeocodeResponse, LocationGeocodeItem
from backend.services.geocoding import geocode_location

router = APIRouter(prefix="/api/locations", tags=["Locations"])


@router.get("/geocode", response_model=LocationGeocodeResponse)
def geocode_query(
    q: str = Query(..., min_length=1, description="Location name, zip, landmark, or coordinates"),
):
    """Geocodes a location query to return primary match and alternative candidates."""
    try:
        data = geocode_location(q)
        primary = None
        if data.get("primary_location"):
            primary = LocationGeocodeItem(**data["primary_location"])

        matches = [LocationGeocodeItem(**m) for m in data.get("all_matches", [])]

        return LocationGeocodeResponse(
            query=q,
            total_matches=data["total_matches"],
            primary_location=primary,
            all_matches=matches,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Geocoding service error: {exc}",
        )

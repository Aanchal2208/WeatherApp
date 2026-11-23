"""Geocoding service using Nominatim (OpenStreetMap).

Handles all location input types:
- City/Town names: "New York", "London"
- ZIP/Postal codes: "10001", "SW1A 1AA"
- GPS coordinates: "40.7128,-74.0060" or "40.7128, -74.0060"
- Landmarks: "Eiffel Tower", "Statue of Liberty"
- Addresses: "1600 Pennsylvania Avenue"
- Countries: "Japan", "France"
"""

import re
import time
import requests
from config import Config

# Rate limiting: Nominatim allows 1 request/second
_last_request_time = 0


def _rate_limit():
    """Ensure at least 1 second between Nominatim requests."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)
    _last_request_time = time.time()


def _is_coordinates(query: str) -> tuple:
    """Check if the query looks like GPS coordinates.

    Returns (lat, lon) tuple if matched, None otherwise.
    Supports formats:
    - "40.7128,-74.0060"
    - "40.7128, -74.0060"
    - "40°42'46\"N 74°0'22\"W" (basic DMS)
    """
    # Decimal format: lat,lon
    pattern = r"^\s*(-?\d+\.?\d*)\s*[,\s]\s*(-?\d+\.?\d*)\s*$"
    match = re.match(pattern, query.strip())
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return (lat, lon)
    return None


def geocode(query: str) -> dict:
    """Resolve a location query to coordinates and place details.

    Args:
        query: Any location string (city, zip, coordinates, landmark, etc.)

    Returns:
        Dictionary with keys: name, latitude, longitude, country,
        display_name, type

    Raises:
        ValueError: If the location cannot be found.
        ConnectionError: If the geocoding service is unavailable.
    """
    query = query.strip()
    if not query:
        raise ValueError("Location query cannot be empty.")

    # Check if it's already GPS coordinates
    coords = _is_coordinates(query)
    if coords:
        return _reverse_geocode(coords[0], coords[1])

    # Forward geocode using Nominatim
    return _forward_geocode(query)


def _forward_geocode(query: str) -> dict:
    """Forward geocode: text → coordinates."""
    _rate_limit()

    try:
        response = requests.get(
            f"{Config.NOMINATIM_URL}/search",
            params={
                "q": query,
                "format": "json",
                "limit": 1,
                "addressdetails": 1,
            },
            headers={"User-Agent": Config.NOMINATIM_USER_AGENT},
            timeout=Config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        results = response.json()
    except requests.exceptions.Timeout:
        raise ConnectionError(
            "Geocoding service timed out. Please try again."
        )
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Unable to reach geocoding service. Check your internet connection."
        )
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Geocoding request failed: {str(e)}")

    if not results:
        raise ValueError(
            f"Location '{query}' not found. Please try a different search term, "
            f"e.g., a city name, zip code, or landmark."
        )

    result = results[0]
    address = result.get("address", {})

    # Build a clean location name
    name_parts = []
    for key in ["city", "town", "village", "hamlet", "municipality"]:
        if key in address:
            name_parts.append(address[key])
            break

    if not name_parts:
        # Fallback to the display name's first component
        name_parts.append(result.get("name", query))

    state = address.get("state", "")
    country = address.get("country", "")

    if state and state not in name_parts:
        name_parts.append(state)
    if country:
        name_parts.append(country)

    return {
        "name": ", ".join(name_parts) if name_parts else result.get("display_name", query),
        "latitude": float(result["lat"]),
        "longitude": float(result["lon"]),
        "country": country,
        "country_code": address.get("country_code", "").upper(),
        "display_name": result.get("display_name", ""),
        "type": result.get("type", "unknown"),
    }


def _reverse_geocode(lat: float, lon: float) -> dict:
    """Reverse geocode: coordinates → place details."""
    _rate_limit()

    try:
        response = requests.get(
            f"{Config.NOMINATIM_URL}/reverse",
            params={
                "lat": lat,
                "lon": lon,
                "format": "json",
                "addressdetails": 1,
            },
            headers={"User-Agent": Config.NOMINATIM_USER_AGENT},
            timeout=Config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as e:
        # If reverse geocoding fails, return raw coordinates
        return {
            "name": f"{lat:.4f}, {lon:.4f}",
            "latitude": lat,
            "longitude": lon,
            "country": "Unknown",
            "country_code": "",
            "display_name": f"Coordinates: {lat}, {lon}",
            "type": "coordinates",
        }

    if "error" in result:
        return {
            "name": f"{lat:.4f}, {lon:.4f}",
            "latitude": lat,
            "longitude": lon,
            "country": "Unknown",
            "country_code": "",
            "display_name": f"Coordinates: {lat}, {lon}",
            "type": "coordinates",
        }

    address = result.get("address", {})
    name_parts = []
    for key in ["city", "town", "village", "hamlet", "municipality"]:
        if key in address:
            name_parts.append(address[key])
            break
    if not name_parts:
        name_parts.append(result.get("name", f"{lat:.4f}, {lon:.4f}"))

    state = address.get("state", "")
    country = address.get("country", "")
    if state:
        name_parts.append(state)
    if country:
        name_parts.append(country)

    return {
        "name": ", ".join(name_parts),
        "latitude": lat,
        "longitude": lon,
        "country": country,
        "country_code": address.get("country_code", "").upper(),
        "display_name": result.get("display_name", ""),
        "type": result.get("type", "coordinates"),
    }

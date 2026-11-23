"""Geocoding service using Open-Meteo Geocoding API with Nominatim (OSM) fallback.

Handles all location input types:
- City/Town names: "New York", "London", "Tokyo"
- ZIP/Postal codes: "10001", "SW1A 1AA", "90210"
- GPS coordinates: "40.7128,-74.0060" or "40.7128, -74.0060"
- Landmarks: "Eiffel Tower", "Statue of Liberty", "Taj Mahal"
- Places/Addresses: "Times Square", "Oxford Street"

Validates the location and returns candidate matches so users can pick
the exact place if multiple matches exist.
"""

import re
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import requests
from backend.config import config

logger = logging.getLogger("weather_app.geocoding")

_last_nominatim_time = 0.0


def _rate_limit_nominatim():
    """Ensure at least 1.1s between Nominatim requests to respect OSM policy."""
    global _last_nominatim_time
    elapsed = time.time() - _last_nominatim_time
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)
    _last_nominatim_time = time.time()


def parse_coordinates(query: str) -> Optional[Tuple[float, float]]:
    """Checks if a string represents decimal GPS coordinates.

    Supports: "40.7128,-74.0060", "40.7128, -74.0060", etc.
    """
    pattern = r"^\s*(-?\d+\.?\d*)\s*[,\s]\s*(-?\d+\.?\d*)\s*$"
    match = re.match(pattern, query.strip())
    if match:
        try:
            lat = float(match.group(1))
            lon = float(match.group(2))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
        except ValueError:
            pass
    return None


def reverse_geocode(lat: float, lon: float) -> Dict[str, Any]:
    """Resolves latitude and longitude to a human-readable location name via Nominatim."""
    _rate_limit_nominatim()
    url = config.NOMINATIM_REVERSE_URL
    headers = {"User-Agent": "WeatherIntelligencePlatform/1.0 (contact: student@pmaccelerator.io)"}
    params = {"lat": lat, "lon": lon, "format": "jsonv2"}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        addr = data.get("address", {})
        name = (
            addr.get("city")
            or addr.get("town")
            or addr.get("village")
            or addr.get("suburb")
            or data.get("name")
            or f"{lat:.4f}, {lon:.4f}"
        )
        country = addr.get("country", "")

        return {
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "country": country,
            "admin1": addr.get("state"),
            "timezone": None,
            "display_name": data.get("display_name", f"{name}, {country}"),
        }
    except Exception as exc:
        logger.warning("Reverse geocoding failed: %s; using coordinates as name", exc)
        return {
            "name": f"{lat:.4f}, {lon:.4f}",
            "latitude": lat,
            "longitude": lon,
            "country": None,
            "admin1": None,
            "timezone": None,
            "display_name": f"Coordinates: {lat:.4f}, {lon:.4f}",
        }


def geocode_location(query: str) -> Dict[str, Any]:
    """Converts a user-provided location query into geocoded candidates.

    Returns a dict with 'primary_location' and 'all_matches'.
    Raises ValueError if no matching location is found.
    """
    query = query.strip()
    if not query:
        raise ValueError("Location query cannot be empty.")

    # 1. Direct GPS coordinates check
    coords = parse_coordinates(query)
    if coords:
        resolved = reverse_geocode(coords[0], coords[1])
        return {
            "query": query,
            "total_matches": 1,
            "primary_location": resolved,
            "all_matches": [resolved],
        }

    matches: List[Dict[str, Any]] = []

    # 2. Open-Meteo Geocoding API (Fast, comprehensive city database)
    try:
        resp = requests.get(
            config.OPEN_METEO_GEOCODING_URL,
            params={"name": query, "count": 10, "language": "en", "format": "json"},
            timeout=config.REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            for r in data.get("results", []):
                matches.append({
                    "name": r.get("name", query),
                    "latitude": float(r.get("latitude")),
                    "longitude": float(r.get("longitude")),
                    "country": r.get("country"),
                    "admin1": r.get("admin1"),
                    "timezone": r.get("timezone"),
                    "display_name": f"{r.get('name')}, {r.get('admin1', '')} {r.get('country', '')}".strip(),
                })
    except Exception as exc:
        logger.warning("Open-Meteo geocoding request failed: %s", exc)

    # 3. Fallback to Nominatim / OpenStreetMap if Open-Meteo returned 0 matches
    # (Useful for landmarks, postal codes, and detailed street addresses)
    if not matches:
        _rate_limit_nominatim()
        headers = {"User-Agent": "WeatherIntelligencePlatform/1.0 (contact: student@pmaccelerator.io)"}
        params = {"q": query, "format": "jsonv2", "limit": 5, "addressdetails": 1}
        try:
            resp = requests.get(
                config.NOMINATIM_GEOCODING_URL,
                params=params,
                headers=headers,
                timeout=config.REQUEST_TIMEOUT,
            )
            if resp.status_code == 200:
                data = resp.json()
                for r in data:
                    addr = r.get("address", {})
                    name = (
                        addr.get("city")
                        or addr.get("town")
                        or addr.get("village")
                        or r.get("name")
                        or query
                    )
                    matches.append({
                        "name": name,
                        "latitude": float(r["lat"]),
                        "longitude": float(r["lon"]),
                        "country": addr.get("country"),
                        "admin1": addr.get("state"),
                        "timezone": None,
                        "display_name": r.get("display_name"),
                    })
        except Exception as exc:
            logger.warning("Nominatim geocoding request failed: %s", exc)

    if not matches:
        raise ValueError(
            f"Location '{query}' could not be resolved. Please verify spelling or try city, zip, or coordinates."
        )

    return {
        "query": query,
        "total_matches": len(matches),
        "primary_location": matches[0],
        "all_matches": matches,
    }

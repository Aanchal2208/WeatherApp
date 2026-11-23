"""External API integrations: YouTube Data API v3, OpenStreetMap Maps, and PM Accelerator."""

import urllib.parse
import logging
from typing import Dict, Any, List
import requests
from backend.config import config

logger = logging.getLogger("weather_app.integrations")

# Official PM Accelerator details
PM_ACCELERATOR_DETAILS = {
    "organization": "PM Accelerator / Product Manager Accelerator",
    "developer": "Aanchal Singh",
    "website": "https://www.pmaccelerator.io/",
    "linkedin": "https://www.linkedin.com/company/product-manager-accelerator/",
    "mission": (
        "The Product Manager Accelerator Program is designed to support product management "
        "professionals through every stage of their career — from students and aspiring PMs "
        "breaking into tech to experienced leaders advancing into Director and VP roles. "
        "Through rigorous technical assessments, end-to-end hands-on curriculum, weekly mentorship, "
        "and tailored career coaching, PM Accelerator equips fellows with real-world skills to land "
        "and thrive in top tier product and engineering roles."
    ),
}


def get_youtube_travel_videos(location_name: str, max_results: int = 4) -> Dict[str, Any]:
    """Retrieves relevant travel guides and tour videos for a given location.

    If YOUTUBE_API_KEY is configured in .env, calls YouTube Data API v3.
    Otherwise, generates a genuine YouTube search URL as a transparent fallback.
    Never pretends an API was called when it was not.
    """
    search_query = f"{location_name} travel guide top attractions walking tour"
    encoded_query = urllib.parse.quote_plus(search_query)
    search_url = f"https://www.youtube.com/results?search_query={encoded_query}"

    api_key = config.YOUTUBE_API_KEY
    if not api_key:
        return {
            "query": location_name,
            "source": "fallback_url",
            "search_url": search_url,
            "videos": [],
            "message": "YouTube API key not configured in .env. A direct search URL has been provided.",
        }

    # Call official YouTube Data API v3
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": search_query,
            "type": "video",
            "maxResults": max_results,
            "key": api_key,
            "videoEmbeddable": "true",
        }
        resp = requests.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            videos: List[Dict[str, str]] = []
            for item in data.get("items", []):
                vid_id = item.get("id", {}).get("videoId", "")
                snippet = item.get("snippet", {})
                thumbs = snippet.get("thumbnails", {}).get("medium", {})
                videos.append({
                    "video_id": vid_id,
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "thumbnail": thumbs.get("url", ""),
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                })
            return {
                "query": location_name,
                "source": "youtube_api_v3",
                "search_url": search_url,
                "videos": videos,
                "message": "Videos retrieved successfully via YouTube Data API v3.",
            }
        else:
            logger.warning("YouTube API error: %s", resp.text)
            return {
                "query": location_name,
                "source": "fallback_url",
                "search_url": search_url,
                "videos": [],
                "message": f"YouTube API returned status {resp.status_code}. Fallback search URL provided.",
            }
    except Exception as exc:
        logger.error("Error communicating with YouTube API: %s", exc)
        return {
            "query": location_name,
            "source": "fallback_url",
            "search_url": search_url,
            "videos": [],
            "message": "Connection error reaching YouTube API. Fallback search URL provided.",
        }


def get_map_metadata(lat: float, lon: float, location_name: str) -> Dict[str, Any]:
    """Returns map configuration and tile server URLs for Leaflet integration."""
    return {
        "location_name": location_name,
        "latitude": lat,
        "longitude": lon,
        "tile_layer": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attribution": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors",
        "default_zoom": 11,
    }

"""Third-party API integrations: YouTube, Wikipedia, RestCountries.

All APIs used here are free and most require no API key.
"""

import requests
from config import Config


# ---------------------------------------------------------------------------
# YouTube Integration
# ---------------------------------------------------------------------------

def search_youtube_videos(query: str, max_results: int = 6) -> dict:
    """Search YouTube for videos related to a location.

    Uses the YouTube Data API v3 if an API key is configured;
    otherwise returns a search URL for manual browsing.

    Args:
        query: Search query (typically location name + "travel"/"tour").
        max_results: Maximum number of video results.

    Returns:
        Dictionary with 'videos' list and 'search_url'.
    """
    import urllib.parse

    search_query = f"{query} travel tour"
    encoded = urllib.parse.quote_plus(search_query)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"

    result = {"search_url": search_url, "videos": [], "source": "url"}

    api_key = Config.YOUTUBE_API_KEY
    if not api_key:
        return result

    try:
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": search_query,
                "type": "video",
                "maxResults": max_results,
                "key": api_key,
                "videoEmbeddable": "true",
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        videos = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            video_id = item.get("id", {}).get("videoId", "")
            videos.append({
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "channel": snippet.get("channelTitle", ""),
                "published_at": snippet.get("publishedAt", ""),
                "embed_url": f"https://www.youtube.com/embed/{video_id}",
                "watch_url": f"https://www.youtube.com/watch?v={video_id}",
            })

        result["videos"] = videos
        result["source"] = "api"

    except requests.exceptions.RequestException:
        # Fallback: return just the search URL
        pass

    return result


# ---------------------------------------------------------------------------
# Wikipedia Integration
# ---------------------------------------------------------------------------

def get_wikipedia_summary(query: str) -> dict:
    """Get a Wikipedia summary for a location.

    Uses the Wikipedia REST API (no key required).

    Args:
        query: Location name to search.

    Returns:
        Dictionary with title, summary, url, and thumbnail.
    """
    title = query
    try:
        # Try the direct REST summary API first (most reliable)
        import urllib.parse
        encoded_query = urllib.parse.quote(query.replace(" ", "_"))
        summary_resp = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_query}",
            headers={"User-Agent": Config.NOMINATIM_USER_AGENT},
            timeout=Config.REQUEST_TIMEOUT,
        )

        # If direct lookup fails, fall back to search
        if summary_resp.status_code == 404:
            search_resp = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "srlimit": 1,
                    "format": "json",
                },
                timeout=Config.REQUEST_TIMEOUT,
            )
            search_resp.raise_for_status()
            search_data = search_resp.json()
            results = search_data.get("query", {}).get("search", [])
            if not results:
                return {"found": False, "query": query}

            title = results[0]["title"]
            encoded_title = urllib.parse.quote(title.replace(" ", "_"))
            summary_resp = requests.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}",
                headers={"User-Agent": Config.NOMINATIM_USER_AGENT},
                timeout=Config.REQUEST_TIMEOUT,
            )

        summary_resp.raise_for_status()
        summary_data = summary_resp.json()

        thumbnail = summary_data.get("thumbnail", {})

        return {
            "found": True,
            "title": summary_data.get("title", title),
            "extract": summary_data.get("extract", ""),
            "description": summary_data.get("description", ""),
            "url": summary_data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "thumbnail_url": thumbnail.get("source", ""),
            "thumbnail_width": thumbnail.get("width", 0),
            "thumbnail_height": thumbnail.get("height", 0),
        }

    except requests.exceptions.RequestException:
        return {"found": False, "query": query, "error": "Wikipedia unavailable"}


# ---------------------------------------------------------------------------
# Country Information Integration
# ---------------------------------------------------------------------------

def get_country_info(country_code: str) -> dict:
    """Get country information using CountriesNow API.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g., "US", "FR").

    Returns:
        Dictionary with country details.
    """
    if not country_code or len(country_code) != 2:
        return {}

    iso2 = country_code.upper()
    info = {
        "name": "",
        "official_name": "",
        "capital": "",
        "region": "",
        "subregion": "",
        "population": 0,
        "area_km2": 0,
        "currencies": [],
        "languages": [],
        "flag_emoji": "",
        "flag_url": "",
        "timezones": [],
        "maps_url": f"https://www.google.com/maps/place/{iso2}",
    }

    try:
        # 1. Capital and common name
        cap_resp = requests.post(
            "https://countriesnow.space/api/v0.1/countries/capital",
            json={"iso2": iso2},
            timeout=Config.REQUEST_TIMEOUT,
        )
        if cap_resp.ok:
            cap_data = cap_resp.json().get("data", {})
            info["name"] = cap_data.get("name", "")
            info["official_name"] = cap_data.get("name", "")
            info["capital"] = cap_data.get("capital", "")

        # 2. Flag
        flag_resp = requests.post(
            "https://countriesnow.space/api/v0.1/countries/flag/unicode",
            json={"iso2": iso2},
            timeout=Config.REQUEST_TIMEOUT,
        )
        if flag_resp.ok:
            flag_data = flag_resp.json().get("data", {})
            info["flag_emoji"] = flag_data.get("unicodeFlag", "")
            if not info["name"]:
                info["name"] = flag_data.get("name", "")

        # 3. Currency
        cur_resp = requests.post(
            "https://countriesnow.space/api/v0.1/countries/currency",
            json={"iso2": iso2},
            timeout=Config.REQUEST_TIMEOUT,
        )
        if cur_resp.ok:
            cur_data = cur_resp.json().get("data", {})
            cur_code = cur_data.get("currency", "")
            if cur_code:
                info["currencies"] = [{"code": cur_code, "name": cur_code, "symbol": cur_code}]

        if not info["name"]:
            return {}

        return info

    except requests.exceptions.RequestException:
        return {}


# ---------------------------------------------------------------------------
# Open-Meteo Marine / Astronomy (bonus creative API)
# ---------------------------------------------------------------------------

def get_sunrise_sunset(latitude: float, longitude: float) -> dict:
    """Get sunrise/sunset and day length data.

    Uses Open-Meteo forecast API with daily sunrise/sunset.
    """
    try:
        response = requests.get(
            Config.OPEN_METEO_FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": "sunrise,sunset,daylight_duration,uv_index_max",
                "timezone": "auto",
                "forecast_days": 1,
            },
            timeout=Config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        daily = data.get("daily", {})

        daylight_seconds = (daily.get("daylight_duration") or [0])[0]
        hours = int(daylight_seconds // 3600)
        minutes = int((daylight_seconds % 3600) // 60)

        return {
            "sunrise": (daily.get("sunrise") or [""])[0],
            "sunset": (daily.get("sunset") or [""])[0],
            "daylight_duration": f"{hours}h {minutes}m",
            "daylight_seconds": daylight_seconds,
            "uv_index_max": (daily.get("uv_index_max") or [None])[0],
        }

    except requests.exceptions.RequestException:
        return {}

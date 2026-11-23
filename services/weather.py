"""Weather service using Open-Meteo API (free, no key required).

Provides:
- Current weather conditions
- Historical daily weather for a date range
- Weather forecast
- Air quality data
"""

import requests
from datetime import date, timedelta
from config import Config

# WMO Weather interpretation codes → human-readable descriptions + icons
WMO_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Foggy", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    56: ("Light freezing drizzle", "🌨️"),
    57: ("Dense freezing drizzle", "🌨️"),
    61: ("Slight rain", "🌦️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Light freezing rain", "🌨️"),
    67: ("Heavy freezing rain", "🌨️"),
    71: ("Slight snowfall", "🌨️"),
    73: ("Moderate snowfall", "❄️"),
    75: ("Heavy snowfall", "❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Slight rain showers", "🌦️"),
    81: ("Moderate rain showers", "🌧️"),
    82: ("Violent rain showers", "⛈️"),
    85: ("Slight snow showers", "🌨️"),
    86: ("Heavy snow showers", "❄️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with slight hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}


def get_weather_description(code: int) -> tuple:
    """Get human-readable description and emoji for a WMO weather code."""
    return WMO_CODES.get(code, ("Unknown", "❓"))


def get_current_weather(latitude: float, longitude: float) -> dict:
    """Fetch current weather conditions for a location.

    Args:
        latitude: Location latitude.
        longitude: Location longitude.

    Returns:
        Dictionary with current weather data.

    Raises:
        ConnectionError: If the weather API is unavailable.
        ValueError: If the API returns an error.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "is_day",
            "precipitation",
            "rain",
            "snowfall",
            "weather_code",
            "cloud_cover",
            "pressure_msl",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
        ]),
        "timezone": "auto",
    }

    try:
        response = requests.get(
            Config.OPEN_METEO_FORECAST_URL,
            params=params,
            timeout=Config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        raise ConnectionError("Weather service timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Unable to reach weather service. Check your internet connection."
        )
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Weather request failed: {str(e)}")

    if "error" in data:
        raise ValueError(f"Weather API error: {data.get('reason', 'Unknown error')}")

    current = data.get("current", {})
    units = data.get("current_units", {})
    weather_code = current.get("weather_code", 0)
    description, icon = get_weather_description(weather_code)

    return {
        "temperature": current.get("temperature_2m"),
        "temperature_unit": units.get("temperature_2m", "°C"),
        "apparent_temperature": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "precipitation": current.get("precipitation"),
        "rain": current.get("rain"),
        "snowfall": current.get("snowfall"),
        "cloud_cover": current.get("cloud_cover"),
        "pressure_msl": current.get("pressure_msl"),
        "surface_pressure": current.get("surface_pressure"),
        "wind_speed": current.get("wind_speed_10m"),
        "wind_speed_unit": units.get("wind_speed_10m", "km/h"),
        "wind_direction": current.get("wind_direction_10m"),
        "wind_gusts": current.get("wind_gusts_10m"),
        "weather_code": weather_code,
        "weather_description": description,
        "weather_icon": icon,
        "is_day": bool(current.get("is_day", 1)),
        "timezone": data.get("timezone", ""),
        "elevation": data.get("elevation"),
        "time": current.get("time", ""),
    }


def get_historical_weather(
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
) -> dict:
    """Fetch historical daily weather for a date range.

    Args:
        latitude: Location latitude.
        longitude: Location longitude.
        start_date: Start of the date range.
        end_date: End of the date range.

    Returns:
        Dictionary with daily weather data arrays.

    Raises:
        ValueError: If dates are invalid or API returns an error.
        ConnectionError: If the API is unavailable.
    """
    today = date.today()

    # Determine which API to use based on dates
    # Archive API: data from 1940 to ~5 days ago
    # Forecast API: last few days + 16 days ahead
    archive_cutoff = today - timedelta(days=5)

    if end_date > today + timedelta(days=16):
        raise ValueError(
            f"End date cannot be more than 16 days in the future. "
            f"Maximum forecast date: {(today + timedelta(days=16)).isoformat()}"
        )

    daily_params = ",".join([
        "weather_code",
        "temperature_2m_max",
        "temperature_2m_min",
        "apparent_temperature_max",
        "apparent_temperature_min",
        "precipitation_sum",
        "rain_sum",
        "snowfall_sum",
        "precipitation_hours",
        "wind_speed_10m_max",
        "wind_gusts_10m_max",
        "wind_direction_10m_dominant",
        "sunrise",
        "sunset",
    ])

    all_daily_data = None

    # If the range spans both archive and forecast periods, merge results
    if start_date < archive_cutoff and end_date >= archive_cutoff:
        # Need to fetch from both APIs
        archive_data = _fetch_weather_range(
            Config.OPEN_METEO_ARCHIVE_URL,
            latitude, longitude,
            start_date, archive_cutoff - timedelta(days=1),
            daily_params,
        )
        forecast_data = _fetch_weather_range(
            Config.OPEN_METEO_FORECAST_URL,
            latitude, longitude,
            archive_cutoff, end_date,
            daily_params,
        )
        all_daily_data = _merge_daily_data(archive_data, forecast_data)
    elif end_date < archive_cutoff:
        # Entirely in archive range
        all_daily_data = _fetch_weather_range(
            Config.OPEN_METEO_ARCHIVE_URL,
            latitude, longitude,
            start_date, end_date,
            daily_params,
        )
    else:
        # Entirely in forecast range
        all_daily_data = _fetch_weather_range(
            Config.OPEN_METEO_FORECAST_URL,
            latitude, longitude,
            start_date, end_date,
            daily_params,
        )

    # Enrich with descriptions
    if all_daily_data and "weather_code" in all_daily_data:
        descriptions = []
        icons = []
        for code in all_daily_data["weather_code"]:
            desc, icon = get_weather_description(code or 0)
            descriptions.append(desc)
            icons.append(icon)
        all_daily_data["weather_description"] = descriptions
        all_daily_data["weather_icon"] = icons

    return all_daily_data


def _fetch_weather_range(
    api_url: str,
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
    daily_params: str,
) -> dict:
    """Fetch weather data from a specific Open-Meteo API endpoint."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": daily_params,
        "timezone": "auto",
    }

    try:
        response = requests.get(
            api_url, params=params, timeout=Config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        raise ConnectionError("Weather service timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Unable to reach weather service. Check your internet connection."
        )
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Weather request failed: {str(e)}")

    if "error" in data:
        raise ValueError(
            f"Weather API error: {data.get('reason', 'Unknown error')}"
        )

    return data.get("daily", {})


def _merge_daily_data(archive: dict, forecast: dict) -> dict:
    """Merge daily data from archive and forecast APIs."""
    merged = {}
    for key in archive:
        archive_vals = archive.get(key, []) or []
        forecast_vals = forecast.get(key, []) or []
        merged[key] = archive_vals + forecast_vals
    return merged


def get_air_quality(latitude: float, longitude: float) -> dict:
    """Fetch current air quality data.

    Returns:
        Dictionary with air quality metrics.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join([
            "us_aqi",
            "pm10",
            "pm2_5",
            "carbon_monoxide",
            "nitrogen_dioxide",
            "ozone",
            "uv_index",
        ]),
    }

    try:
        response = requests.get(
            Config.OPEN_METEO_AIR_QUALITY_URL,
            params=params,
            timeout=Config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException:
        # Air quality is supplementary — return empty on failure
        return {}

    current = data.get("current", {})
    aqi = current.get("us_aqi", 0)

    # AQI category
    if aqi <= 50:
        aqi_label, aqi_color = "Good", "green"
    elif aqi <= 100:
        aqi_label, aqi_color = "Moderate", "yellow"
    elif aqi <= 150:
        aqi_label, aqi_color = "Unhealthy for Sensitive Groups", "orange"
    elif aqi <= 200:
        aqi_label, aqi_color = "Unhealthy", "red"
    elif aqi <= 300:
        aqi_label, aqi_color = "Very Unhealthy", "purple"
    else:
        aqi_label, aqi_color = "Hazardous", "maroon"

    return {
        "aqi": aqi,
        "aqi_label": aqi_label,
        "aqi_color": aqi_color,
        "pm10": current.get("pm10"),
        "pm2_5": current.get("pm2_5"),
        "carbon_monoxide": current.get("carbon_monoxide"),
        "nitrogen_dioxide": current.get("nitrogen_dioxide"),
        "ozone": current.get("ozone"),
        "uv_index": current.get("uv_index"),
    }

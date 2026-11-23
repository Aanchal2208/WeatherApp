"""Weather service communicating with Open-Meteo APIs.

Features:
- Live current weather conditions
- Open-Meteo Historical Archive API (for past dates)
- Open-Meteo Forecast API (for upcoming dates up to +16 days)
- Air quality metrics (AQI, PM2.5, PM10, Ozone, UV Index)
- Rule-based explainable activity and clothing recommendations
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
import requests
from backend.config import config

logger = logging.getLogger("weather_app.weather")

# WMO Weather interpretation codes mapped to descriptions and emojis
WMO_CODES: Dict[int, Tuple[str, str]] = {
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
    71: ("Slight snowfall", "❄️"),
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


def get_wmo_info(code: Optional[int]) -> Tuple[str, str]:
    """Returns human-readable text and emoji for a WMO code."""
    if code is None:
        return "Unknown", "❓"
    return WMO_CODES.get(code, ("Unknown", "❓"))


def generate_recommendations(
    temperature: float,
    weather_code: int,
    wind_speed: float,
    precipitation: float,
) -> Dict[str, str]:
    """Generates rule-based, fully explainable weather recommendations."""
    # 1. Activity advice based on precipitation and conditions
    is_rain = weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99] or precipitation > 1.0
    is_snow = weather_code in [56, 57, 66, 67, 71, 73, 75, 77, 85, 86]
    is_clear = weather_code in [0, 1]

    if is_rain:
        activity = "Indoor activities recommended (museums, cafes, galleries)"
        advice = "Carry a waterproof umbrella and rain jacket. Road surfaces may be slippery."
    elif is_snow:
        activity = "Winter sports or cozy indoor leisure"
        advice = "Watch out for icy sidewalks and reduced visibility. Drive cautiously."
    elif is_clear and 18 <= temperature <= 26:
        activity = "Ideal for outdoor sightseeing, parks, and walking tours"
        advice = "Enjoy the comfortable outdoor weather! Perfect conditions for photography."
    else:
        activity = "Standard outdoor or indoor activities"
        advice = "Check local forecasts if planning extended outdoor trips."

    # 2. Clothing advice based on temperature
    if temperature < 0:
        clothing = "Heavy winter coat, thermal innerwear, gloves, beanie, insulated boots"
    elif 0 <= temperature < 10:
        clothing = "Warm winter jacket, sweater, scarf, and long pants"
    elif 10 <= temperature < 18:
        clothing = "Light jacket, sweater, or hoodie with comfortable layers"
    elif 18 <= temperature < 26:
        clothing = "Breathable t-shirt, jeans/chinos, light jacket for evening"
    elif 26 <= temperature < 32:
        clothing = "Lightweight cotton/linen clothes, sunglasses, and sun hat"
    else:
        clothing = "Loose, light-colored clothing, high-SPF sunscreen, and sunglasses"

    # 3. Precautions based on wind and heat/cold extremes
    precautions_list = []
    if wind_speed > 35:
        precautions_list.append("High wind warning: secure loose outdoor items and be careful near tall trees.")
    elif wind_speed > 25:
        precautions_list.append("Breezy conditions: keep light personal items secure.")

    if temperature > 32:
        precautions_list.append("High heat caution: stay hydrated and avoid prolonged direct sun exposure between 12-4 PM.")
    elif temperature < 5:
        precautions_list.append("Cold chill caution: limit prolonged skin exposure to freezing winds.")

    if not precautions_list:
        precautions_list.append("Normal weather conditions: no severe environmental alerts.")

    return {
        "activity_type": activity,
        "advice": advice,
        "clothing": clothing,
        "precautions": " ".join(precautions_list),
    }


def fetch_air_quality(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """Fetches air quality indices and particulate measurements from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "european_aqi,us_aqi,pm10,pm2_5,ozone,uv_index",
    }
    try:
        resp = requests.get(
            config.OPEN_METEO_AIR_QUALITY_URL,
            params=params,
            timeout=config.REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json().get("current", {})
            aqi_val = data.get("us_aqi") or data.get("european_aqi")

            category = "Good"
            if aqi_val:
                if aqi_val <= 50:
                    category = "Good"
                elif aqi_val <= 100:
                    category = "Moderate"
                elif aqi_val <= 150:
                    category = "Unhealthy for Sensitive Groups"
                elif aqi_val <= 200:
                    category = "Unhealthy"
                else:
                    category = "Very Unhealthy"

            return {
                "aqi": aqi_val,
                "pm2_5": data.get("pm2_5"),
                "pm10": data.get("pm10"),
                "ozone": data.get("ozone"),
                "uv_index": data.get("uv_index"),
                "category": category,
            }
    except Exception as exc:
        logger.warning("Air quality fetch failed: %s", exc)
    return None


def get_current_weather(lat: float, lon: float) -> Dict[str, Any]:
    """Fetches real-time current weather from Open-Meteo Forecast API."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "is_day,precipitation,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m"
        ),
        "daily": "sunrise,sunset",
        "timezone": "auto",
    }

    resp = requests.get(
        config.OPEN_METEO_FORECAST_URL,
        params=params,
        timeout=config.REQUEST_TIMEOUT,
    )
    if resp.status_code != 200:
        raise ValueError(f"Open-Meteo API returned error status {resp.status_code}: {resp.text}")

    payload = resp.json()
    curr = payload.get("current", {})
    daily = payload.get("daily", {})

    weather_code = curr.get("weather_code", 0)
    desc, icon = get_wmo_info(weather_code)

    temperature = float(curr.get("temperature_2m", 0.0))
    apparent_temp = float(curr.get("apparent_temperature", temperature))
    humidity = float(curr.get("relative_humidity_2m", 0.0))
    wind_speed = float(curr.get("wind_speed_10m", 0.0))
    wind_direction = float(curr.get("wind_direction_10m", 0.0))
    precipitation = float(curr.get("precipitation", 0.0))
    surface_pressure = float(curr.get("surface_pressure", 1013.25))

    sunrise_list = daily.get("sunrise", [])
    sunset_list = daily.get("sunset", [])
    sunrise = sunrise_list[0] if sunrise_list else None
    sunset = sunset_list[0] if sunset_list else None

    # Recommendations
    recommendations = generate_recommendations(
        temperature=temperature,
        weather_code=weather_code,
        wind_speed=wind_speed,
        precipitation=precipitation,
    )

    # Air quality
    air_quality = fetch_air_quality(lat, lon)

    return {
        "weather": {
            "temperature": temperature,
            "apparent_temperature": apparent_temp,
            "relative_humidity": humidity,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "precipitation": precipitation,
            "surface_pressure": surface_pressure,
            "weather_code": weather_code,
            "weather_description": desc,
            "weather_icon": icon,
            "is_day": curr.get("is_day", 1),
            "time": curr.get("time", datetime.now().isoformat()),
        },
        "air_quality": air_quality,
        "recommendations": recommendations,
        "sunrise": sunrise,
        "sunset": sunset,
        "local_time": curr.get("time"),
        "timezone": payload.get("timezone"),
    }


def fetch_weather_range(
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
) -> Dict[str, Any]:
    """Fetches daily weather for a given date range using Open-Meteo APIs.

    Intelligently routes past dates to Open-Meteo Archive API and upcoming
    dates to Forecast API, merging results if necessary.
    """
    today = date.today()
    archive_threshold = today - timedelta(days=2)

    daily_vars = (
        "temperature_2m_max,temperature_2m_min,apparent_temperature_max,"
        "apparent_temperature_min,precipitation_sum,rain_sum,snowfall_sum,"
        "wind_speed_10m_max,weather_code,sunrise,sunset"
    )

    all_days: Dict[str, Dict[str, Any]] = {}

    def query_api(url: str, s_date: date, e_date: date):
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": s_date.isoformat(),
            "end_date": e_date.isoformat(),
            "daily": daily_vars,
            "timezone": "auto",
        }
        res = requests.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
        if res.status_code != 200:
            raise ValueError(f"Weather API error ({res.status_code}): {res.text}")
        data = res.json().get("daily", {})
        times = data.get("time", [])
        for i, dt_str in enumerate(times):
            t_max = data.get("temperature_2m_max", [None])[i]
            t_min = data.get("temperature_2m_min", [None])[i]
            t_mean = None
            if t_max is not None and t_min is not None:
                t_mean = round((t_max + t_min) / 2.0, 2)

            w_code = data.get("weather_code", [0])[i]
            desc, _ = get_wmo_info(w_code)

            all_days[dt_str] = {
                "date": dt_str,
                "temp_max": t_max,
                "temp_min": t_min,
                "temp_mean": t_mean,
                "apparent_temp_max": data.get("apparent_temperature_max", [None])[i],
                "apparent_temp_min": data.get("apparent_temperature_min", [None])[i],
                "precipitation_sum": data.get("precipitation_sum", [None])[i],
                "rain_sum": data.get("rain_sum", [None])[i],
                "snowfall_sum": data.get("snowfall_sum", [None])[i],
                "wind_speed_max": data.get("wind_speed_10m_max", [None])[i],
                "weather_code": w_code,
                "weather_description": desc,
                "sunrise": data.get("sunrise", [None])[i],
                "sunset": data.get("sunset", [None])[i],
            }

    # Case 1: Entire range is in the historical past
    if end_date < archive_threshold:
        query_api(config.OPEN_METEO_ARCHIVE_URL, start_date, end_date)
    # Case 2: Entire range is recent or forecast
    elif start_date >= archive_threshold:
        query_api(config.OPEN_METEO_FORECAST_URL, start_date, end_date)
    # Case 3: Range spans across both archive and forecast
    else:
        query_api(config.OPEN_METEO_ARCHIVE_URL, start_date, archive_threshold - timedelta(days=1))
        query_api(config.OPEN_METEO_FORECAST_URL, archive_threshold, end_date)

    sorted_records = [all_days[k] for k in sorted(all_days.keys())]

    # Compute aggregate summary statistics
    t_maxes = [d["temp_max"] for d in sorted_records if d.get("temp_max") is not None]
    t_mins = [d["temp_min"] for d in sorted_records if d.get("temp_min") is not None]
    precips = [d["precipitation_sum"] for d in sorted_records if d.get("precipitation_sum") is not None]

    summary = {
        "days_count": len(sorted_records),
        "overall_temp_max": max(t_maxes) if t_maxes else None,
        "overall_temp_min": min(t_mins) if t_mins else None,
        "overall_temp_avg": round(sum(t_maxes + t_mins) / (len(t_maxes) + len(t_mins)), 2) if (t_maxes and t_mins) else None,
        "total_precipitation": round(sum(precips), 2) if precips else 0.0,
    }

    return {
        "summary": summary,
        "daily_records": sorted_records,
    }

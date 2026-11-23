"""Application configuration."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Flask application configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///weather.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Optional API keys
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

    # Open-Meteo endpoints (free, no key required)
    OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
    OPEN_METEO_AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

    # Nominatim (OpenStreetMap) geocoding (free, no key required)
    NOMINATIM_URL = "https://nominatim.openstreetmap.org"

    # Request settings
    REQUEST_TIMEOUT = 15  # seconds
    NOMINATIM_USER_AGENT = "WeatherApp/1.0 (tech-assessment)"

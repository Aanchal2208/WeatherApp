"""Configuration settings for Assessment 1 — Weather Application."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory for Assessment 1
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file if present
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")


class Config:
    """Application configuration parameters."""

    # Project metadata
    PROJECT_NAME: str = "Weather Intelligence Platform — Assessment 1"
    DEVELOPER: str = "Aanchal Singh"
    ORGANIZATION: str = "PM Accelerator / Product Manager Accelerator"
    VERSION: str = "1.0.0"

    # PostgreSQL Database Connection URL
    # Default connects to local PostgreSQL 17 on standard port 5432
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/weather_db",
    )

    # Database connection pool settings
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_TIMEOUT: int = int(os.getenv("DB_TIMEOUT", "10"))

    # External APIs
    OPEN_METEO_FORECAST_URL: str = "https://api.open-meteo.com/v1/forecast"
    OPEN_METEO_ARCHIVE_URL: str = "https://archive-api.open-meteo.com/v1/archive"
    OPEN_METEO_GEOCODING_URL: str = "https://geocoding-api.open-meteo.com/v1/search"
    OPEN_METEO_AIR_QUALITY_URL: str = "https://air-quality-api.open-meteo.com/v1/air-quality"
    NOMINATIM_GEOCODING_URL: str = "https://nominatim.openstreetmap.org/search"
    NOMINATIM_REVERSE_URL: str = "https://nominatim.openstreetmap.org/reverse"

    # YouTube Data API v3 (optional key; genuine search URL fallback provided)
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")

    # Network timeout in seconds for external requests
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "15"))

    # Export storage directory
    EXPORT_DIR: Path = BASE_DIR / "exports"


config = Config()

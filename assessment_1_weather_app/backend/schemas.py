"""Pydantic schemas for data validation and API serialization."""

from datetime import date, datetime, timedelta
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, model_validator, ConfigDict


# ---------------------------------------------------------------------------
# Geocoding & Location Schemas
# ---------------------------------------------------------------------------

class LocationGeocodeItem(BaseModel):
    name: str
    latitude: float
    longitude: float
    country: Optional[str] = None
    admin1: Optional[str] = None
    timezone: Optional[str] = None
    display_name: Optional[str] = None


class LocationGeocodeResponse(BaseModel):
    query: str
    total_matches: int
    primary_location: Optional[LocationGeocodeItem] = None
    all_matches: List[LocationGeocodeItem] = []


# ---------------------------------------------------------------------------
# Weather Search & CRUD Schemas
# ---------------------------------------------------------------------------

class DailyWeatherSchema(BaseModel):
    id: Optional[int] = None
    record_id: Optional[int] = None
    date: str
    temp_max: Optional[float] = None
    temp_min: Optional[float] = None
    temp_mean: Optional[float] = None
    apparent_temp_max: Optional[float] = None
    apparent_temp_min: Optional[float] = None
    precipitation_sum: Optional[float] = None
    rain_sum: Optional[float] = None
    snowfall_sum: Optional[float] = None
    wind_speed_max: Optional[float] = None
    weather_code: Optional[int] = None
    weather_description: Optional[str] = None
    sunrise: Optional[str] = None
    sunset: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class WeatherSearchRequest(BaseModel):
    """Payload to search and save a historical or forecast weather record."""

    location: str = Field(..., min_length=1, description="City, zip, landmark, or coords")
    date_start: date = Field(..., description="Start date (YYYY-MM-DD)")
    date_end: date = Field(..., description="End date (YYYY-MM-DD)")

    @model_validator(mode="after")
    def validate_dates(self):
        start = self.date_start
        end = self.date_end
        today = date.today()

        if start > end:
            raise ValueError("Start date cannot be after end date.")

        # Minimum historical date supported by Open-Meteo archive is 1940-01-01
        min_date = date(1940, 1, 1)
        if start < min_date:
            raise ValueError(f"Start date cannot be earlier than {min_date.isoformat()}.")

        # Maximum forecast date supported is roughly +16 days
        max_date = today + timedelta(days=16)
        if end > max_date:
            raise ValueError(
                f"End date cannot exceed {max_date.isoformat()} (max 16-day forecast limit)."
            )

        return self


class WeatherRecordUpdateRequest(BaseModel):
    """Payload to edit an existing record's location and/or date range."""

    location: Optional[str] = Field(None, min_length=1)
    date_start: Optional[date] = None
    date_end: Optional[date] = None

    @model_validator(mode="after")
    def validate_update(self):
        if self.date_start and self.date_end:
            if self.date_start > self.date_end:
                raise ValueError("Start date cannot be after end date.")
        return self


class WeatherRecordResponse(BaseModel):
    id: int
    location_query: str
    location_name: str
    latitude: float
    longitude: float
    country: Optional[str] = None
    timezone: Optional[str] = None
    date_start: str
    date_end: str
    weather_data: Dict[str, Any]
    daily_records: List[DailyWeatherSchema] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedWeatherRecordsResponse(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    items: List[WeatherRecordResponse]


# ---------------------------------------------------------------------------
# Current Weather & Recommendations Schemas
# ---------------------------------------------------------------------------

class CurrentWeatherDetail(BaseModel):
    temperature: float
    apparent_temperature: float
    relative_humidity: float
    wind_speed: float
    wind_direction: float
    precipitation: float
    surface_pressure: float
    weather_code: int
    weather_description: str
    weather_icon: str
    is_day: int
    time: str


class AirQualityDetail(BaseModel):
    aqi: Optional[float] = None
    pm2_5: Optional[float] = None
    pm10: Optional[float] = None
    ozone: Optional[float] = None
    uv_index: Optional[float] = None
    category: Optional[str] = None


class RecommendationDetail(BaseModel):
    activity_type: str
    advice: str
    clothing: str
    precautions: str


class CurrentWeatherResponse(BaseModel):
    location: LocationGeocodeItem
    weather: CurrentWeatherDetail
    air_quality: Optional[AirQualityDetail] = None
    recommendations: Optional[RecommendationDetail] = None
    sunrise: Optional[str] = None
    sunset: Optional[str] = None
    local_time: Optional[str] = None


# ---------------------------------------------------------------------------
# Third-Party Integrations Schemas
# ---------------------------------------------------------------------------

class YouTubeVideoItem(BaseModel):
    video_id: str
    title: str
    description: str
    thumbnail: str
    url: str


class YouTubeResponse(BaseModel):
    query: str
    source: str
    search_url: str
    videos: List[YouTubeVideoItem] = []


# ---------------------------------------------------------------------------
# Health Response Schema
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    project: str
    developer: str
    organization: str
    database: Dict[str, Any]
    apis: Dict[str, Any]

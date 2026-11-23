"""FastAPI router for weather queries and CRUD operations.

Demonstrates complete CRUD workflow:
- CREATE: POST /api/weather/search
- READ:   GET /api/weather/records, GET /api/weather/records/{id}
- UPDATE: PUT /api/weather/records/{id}
- DELETE: DELETE /api/weather/records/{id}
- CURRENT: GET /api/weather/current
"""

import json
import math
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from backend.database import get_db
from backend.models import WeatherRecord, DailyWeatherRecord
from backend.schemas import (
    WeatherSearchRequest,
    WeatherRecordUpdateRequest,
    WeatherRecordResponse,
    PaginatedWeatherRecordsResponse,
    CurrentWeatherResponse,
    LocationGeocodeItem,
)
from backend.services.geocoding import geocode_location, reverse_geocode, parse_coordinates
from backend.services.weather import get_current_weather, fetch_weather_range

router = APIRouter(prefix="/api/weather", tags=["Weather"])


@router.get("/current", response_model=CurrentWeatherResponse)
def get_current_conditions(
    q: Optional[str] = Query(None, description="City, zip, coordinates, or landmark"),
    lat: Optional[float] = Query(None, ge=-90, le=90),
    lon: Optional[float] = Query(None, ge=-180, le=180),
):
    """Fetches real-time current weather conditions, AQI, and recommendations.

    Accepts either a text search query `q` or explicit GPS coordinates `lat` and `lon`.
    """
    if lat is not None and lon is not None:
        loc_meta = reverse_geocode(lat, lon)
    elif q:
        geo_result = geocode_location(q)
        loc_meta = geo_result["primary_location"]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either location query 'q' or coordinates ('lat' and 'lon').",
        )

    weather_data = get_current_weather(loc_meta["latitude"], loc_meta["longitude"])

    loc_item = LocationGeocodeItem(
        name=loc_meta["name"],
        latitude=loc_meta["latitude"],
        longitude=loc_meta["longitude"],
        country=loc_meta.get("country"),
        admin1=loc_meta.get("admin1"),
        timezone=weather_data.get("timezone"),
        display_name=loc_meta.get("display_name"),
    )

    return CurrentWeatherResponse(
        location=loc_item,
        weather=weather_data["weather"],
        air_quality=weather_data.get("air_quality"),
        recommendations=weather_data.get("recommendations"),
        sunrise=weather_data.get("sunrise"),
        sunset=weather_data.get("sunset"),
        local_time=weather_data.get("local_time"),
    )


@router.post("/search", response_model=WeatherRecordResponse, status_code=status.HTTP_201_CREATED)
def search_and_create_weather_record(
    payload: WeatherSearchRequest,
    db: Session = Depends(get_db),
):
    """CREATE: Geocodes location, fetches date-range weather from Open-Meteo,

    and persists parent WeatherRecord and normalized DailyWeatherRecord rows to PostgreSQL.
    """
    # 1. Geocode location
    geo = geocode_location(payload.location)
    primary = geo["primary_location"]

    lat = primary["latitude"]
    lon = primary["longitude"]

    # 2. Fetch daily weather observations from Open-Meteo
    weather_results = fetch_weather_range(
        lat=lat,
        lon=lon,
        start_date=payload.date_start,
        end_date=payload.date_end,
    )

    # 3. Create parent record
    parent_record = WeatherRecord(
        location_query=payload.location,
        location_name=primary["name"],
        latitude=lat,
        longitude=lon,
        country=primary.get("country"),
        timezone=primary.get("timezone"),
        date_start=payload.date_start,
        date_end=payload.date_end,
        weather_data=json.dumps(weather_results["summary"]),
    )

    db.add(parent_record)
    db.flush()  # Populates parent_record.id for foreign keys

    # 4. Create child daily records in the same transaction
    for item in weather_results["daily_records"]:
        d_rec = DailyWeatherRecord(
            record_id=parent_record.id,
            date=date.fromisoformat(item["date"]),
            temp_max=item.get("temp_max"),
            temp_min=item.get("temp_min"),
            temp_mean=item.get("temp_mean"),
            apparent_temp_max=item.get("apparent_temp_max"),
            apparent_temp_min=item.get("apparent_temp_min"),
            precipitation_sum=item.get("precipitation_sum"),
            rain_sum=item.get("rain_sum"),
            snowfall_sum=item.get("snowfall_sum"),
            wind_speed_max=item.get("wind_speed_max"),
            weather_code=item.get("weather_code"),
            weather_description=item.get("weather_description"),
            sunrise=item.get("sunrise"),
            sunset=item.get("sunset"),
        )
        db.add(d_rec)

    db.commit()
    db.refresh(parent_record)

    return parent_record.to_dict()


@router.get("/records", response_model=PaginatedWeatherRecordsResponse)
def list_weather_records(
    q: Optional[str] = Query(None, description="Search filter by location or country"),
    date_start: Optional[date] = Query(None, description="Filter records starting on or after date"),
    date_end: Optional[date] = Query(None, description="Filter records ending on or before date"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Records per page"),
    db: Session = Depends(get_db),
):
    """READ: Lists saved weather queries with pagination and flexible filtering."""
    query = db.query(WeatherRecord)

    # Text filter across query, resolved name, and country
    if q:
        like_expr = f"%{q.strip()}%"
        query = query.filter(
            or_(
                WeatherRecord.location_name.ilike(like_expr),
                WeatherRecord.location_query.ilike(like_expr),
                WeatherRecord.country.ilike(like_expr),
            )
        )

    # Date range filters
    if date_start:
        query = query.filter(WeatherRecord.date_start >= date_start)
    if date_end:
        query = query.filter(WeatherRecord.date_end <= date_end)

    total = query.count()
    total_pages = max(1, math.ceil(total / per_page))

    # Paginate and order by newest first
    records = (
        query.order_by(desc(WeatherRecord.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return PaginatedWeatherRecordsResponse(
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        items=[r.to_dict() for r in records],
    )


@router.get("/records/{record_id}", response_model=WeatherRecordResponse)
def get_weather_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """READ: Retrieves a single weather record and its complete daily observation breakdown."""
    rec = db.query(WeatherRecord).filter(WeatherRecord.id == record_id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weather record with ID {record_id} not found.",
        )
    return rec.to_dict()


@router.put("/records/{record_id}", response_model=WeatherRecordResponse)
def update_weather_record(
    record_id: int,
    payload: WeatherRecordUpdateRequest,
    db: Session = Depends(get_db),
):
    """UPDATE: Updates a saved record's location and/or date range.

    Re-validates inputs, re-fetches live weather data from Open-Meteo,
    and updates parent and child records in an atomic database transaction.
    """
    rec = db.query(WeatherRecord).filter(WeatherRecord.id == record_id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weather record with ID {record_id} not found.",
        )

    target_location = payload.location or rec.location_query
    target_start = payload.date_start or rec.date_start
    target_end = payload.date_end or rec.date_end

    if target_start > target_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be after end date.",
        )

    # Re-geocode if location changed
    lat = rec.latitude
    lon = rec.longitude
    loc_name = rec.location_name
    country = rec.country
    tz = rec.timezone

    if payload.location and payload.location != rec.location_query:
        geo = geocode_location(payload.location)
        primary = geo["primary_location"]
        lat = primary["latitude"]
        lon = primary["longitude"]
        loc_name = primary["name"]
        country = primary.get("country")
        tz = primary.get("timezone")

    # Re-fetch weather data for the new parameters
    weather_results = fetch_weather_range(
        lat=lat,
        lon=lon,
        start_date=target_start,
        end_date=target_end,
    )

    # Perform database update in an atomic transaction
    rec.location_query = target_location
    rec.location_name = loc_name
    rec.latitude = lat
    rec.longitude = lon
    rec.country = country
    rec.timezone = tz
    rec.date_start = target_start
    rec.date_end = target_end
    rec.weather_data = json.dumps(weather_results["summary"])

    # Remove existing daily children and recreate them
    db.query(DailyWeatherRecord).filter(DailyWeatherRecord.record_id == rec.id).delete()

    for item in weather_results["daily_records"]:
        d_rec = DailyWeatherRecord(
            record_id=rec.id,
            date=date.fromisoformat(item["date"]),
            temp_max=item.get("temp_max"),
            temp_min=item.get("temp_min"),
            temp_mean=item.get("temp_mean"),
            apparent_temp_max=item.get("apparent_temp_max"),
            apparent_temp_min=item.get("apparent_temp_min"),
            precipitation_sum=item.get("precipitation_sum"),
            rain_sum=item.get("rain_sum"),
            snowfall_sum=item.get("snowfall_sum"),
            wind_speed_max=item.get("wind_speed_max"),
            weather_code=item.get("weather_code"),
            weather_description=item.get("weather_description"),
            sunrise=item.get("sunrise"),
            sunset=item.get("sunset"),
        )
        db.add(d_rec)

    db.commit()
    db.refresh(rec)

    return rec.to_dict()


@router.delete("/records/{record_id}", status_code=status.HTTP_200_OK)
def delete_weather_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """DELETE: Permanently removes a saved weather query.

    Cascading foreign keys in PostgreSQL ensure all associated
    DailyWeatherRecord items are cleanly removed without orphaned rows.
    """
    rec = db.query(WeatherRecord).filter(WeatherRecord.id == record_id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weather record with ID {record_id} not found.",
        )

    loc_name = rec.location_name
    db.delete(rec)
    db.commit()

    return {
        "success": True,
        "message": f"Weather record {record_id} for '{loc_name}' was successfully deleted.",
    }

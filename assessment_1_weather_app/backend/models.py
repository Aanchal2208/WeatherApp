"""SQLAlchemy ORM models for Weather Application.

Demonstrates relational database schema design with:
- Primary keys and automated indexes for fast query lookup
- Normalized 1-to-many relationship (WeatherRecord -> DailyWeatherRecord)
- Foreign key constraints with ON DELETE CASCADE to guarantee referential integrity
- Automatic timestamps using server_default and onupdate
"""

import json
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    Text,
    ForeignKey,
    func,
    Index,
)
from sqlalchemy.orm import relationship
from backend.database import Base


class WeatherRecord(Base):
    """Parent model storing a user's weather search query, resolved location,

    date bounds, and overall weather payload.
    """

    __tablename__ = "weather_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # What the user originally searched for (e.g., "Paris", "10001", "40.71,-74.00")
    location_query = Column(String(255), nullable=False, index=True)

    # Geocoded location details
    location_name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    country = Column(String(100), nullable=True)
    timezone = Column(String(100), nullable=True)

    # Date range for the weather query
    date_start = Column(Date, nullable=False, index=True)
    date_end = Column(Date, nullable=False, index=True)

    # Complete raw/summary weather data payload as JSON string
    weather_data = Column(Text, nullable=False)

    # Audit timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Normalized child relationship: One search record has multiple daily records
    # cascade="all, delete-orphan" ensures child records are automatically deleted
    daily_records = relationship(
        "DailyWeatherRecord",
        back_populates="weather_record",
        cascade="all, delete-orphan",
        order_by="DailyWeatherRecord.date",
    )

    def to_dict(self):
        """Serialize model to a dictionary representation."""
        parsed_data = {}
        if self.weather_data:
            try:
                parsed_data = (
                    json.loads(self.weather_data)
                    if isinstance(self.weather_data, str)
                    else self.weather_data
                )
            except Exception:
                parsed_data = {"raw": self.weather_data}

        return {
            "id": self.id,
            "location_query": self.location_query,
            "location_name": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "country": self.country,
            "timezone": self.timezone,
            "date_start": self.date_start.isoformat() if self.date_start else None,
            "date_end": self.date_end.isoformat() if self.date_end else None,
            "weather_data": parsed_data,
            "daily_records": [d.to_dict() for d in (self.daily_records or [])],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return (
            f"<WeatherRecord(id={self.id}, location='{self.location_name}', "
            f"range={self.date_start}..{self.date_end})>"
        )


class DailyWeatherRecord(Base):
    """Normalized child table storing individual daily observations for a search record.

    Allows direct relational queries, aggregation, and filtering across specific days.
    """

    __tablename__ = "daily_weather_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign key referencing parent record with CASCADE delete
    record_id = Column(
        Integer,
        ForeignKey("weather_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    date = Column(Date, nullable=False, index=True)
    temp_max = Column(Float, nullable=True)
    temp_min = Column(Float, nullable=True)
    temp_mean = Column(Float, nullable=True)
    apparent_temp_max = Column(Float, nullable=True)
    apparent_temp_min = Column(Float, nullable=True)
    precipitation_sum = Column(Float, nullable=True)
    rain_sum = Column(Float, nullable=True)
    snowfall_sum = Column(Float, nullable=True)
    wind_speed_max = Column(Float, nullable=True)
    weather_code = Column(Integer, nullable=True)
    weather_description = Column(String(100), nullable=True)
    sunrise = Column(String(50), nullable=True)
    sunset = Column(String(50), nullable=True)

    # Parent relationship
    weather_record = relationship("WeatherRecord", back_populates="daily_records")

    def to_dict(self):
        return {
            "id": self.id,
            "record_id": self.record_id,
            "date": self.date.isoformat() if self.date else None,
            "temp_max": self.temp_max,
            "temp_min": self.temp_min,
            "temp_mean": self.temp_mean,
            "apparent_temp_max": self.apparent_temp_max,
            "apparent_temp_min": self.apparent_temp_min,
            "precipitation_sum": self.precipitation_sum,
            "rain_sum": self.rain_sum,
            "snowfall_sum": self.snowfall_sum,
            "wind_speed_max": self.wind_speed_max,
            "weather_code": self.weather_code,
            "weather_description": self.weather_description,
            "sunrise": self.sunrise,
            "sunset": self.sunset,
        }

    def __repr__(self):
        return (
            f"<DailyWeatherRecord(id={self.id}, record_id={self.record_id}, "
            f"date={self.date}, temp_max={self.temp_max})>"
        )


# Explicit composite index on record_id and date for fast ordered lookups
Index("idx_daily_record_date", DailyWeatherRecord.record_id, DailyWeatherRecord.date)

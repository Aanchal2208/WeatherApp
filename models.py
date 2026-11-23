"""Database models for the Weather App."""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class WeatherRecord(db.Model):
    """Stores weather query results for CRUD operations.

    Each record represents a user's weather query for a specific location
    and date range, along with the fetched weather data.
    """

    __tablename__ = "weather_records"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # What the user originally typed (e.g., "New York", "10001", "48.8566,2.3522")
    location_query = db.Column(db.String(255), nullable=False)

    # Resolved location details
    location_name = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    country = db.Column(db.String(100), nullable=True)
    timezone = db.Column(db.String(100), nullable=True)

    # Date range for the weather query
    date_start = db.Column(db.Date, nullable=False)
    date_end = db.Column(db.Date, nullable=False)

    # Weather data stored as JSON string
    weather_data = db.Column(db.Text, nullable=False)

    # Metadata
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        """Serialize the record to a dictionary."""
        import json

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
            "weather_data": json.loads(self.weather_data)
            if isinstance(self.weather_data, str)
            else self.weather_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return (
            f"<WeatherRecord id={self.id} location='{self.location_name}' "
            f"dates={self.date_start}..{self.date_end}>"
        )

"""Tests for database CRUD operations and relational integrity."""

import json
from datetime import date
from sqlalchemy.orm import Session
from backend.models import WeatherRecord, DailyWeatherRecord


def test_create_and_read_weather_record(db_session: Session):
    # CREATE
    record = WeatherRecord(
        location_query="Tokyo",
        location_name="Tokyo",
        latitude=35.6762,
        longitude=139.6503,
        country="Japan",
        timezone="Asia/Tokyo",
        date_start=date(2026, 3, 1),
        date_end=date(2026, 3, 3),
        weather_data=json.dumps({"summary": "Sunny spring days"}),
    )
    db_session.add(record)
    db_session.flush()

    daily1 = DailyWeatherRecord(
        record_id=record.id,
        date=date(2026, 3, 1),
        temp_max=16.5,
        temp_min=8.0,
        temp_mean=12.2,
        precipitation_sum=0.0,
        wind_speed_max=12.0,
        weather_code=0,
        weather_description="Clear sky",
    )
    daily2 = DailyWeatherRecord(
        record_id=record.id,
        date=date(2026, 3, 2),
        temp_max=18.0,
        temp_min=9.5,
        temp_mean=13.7,
        precipitation_sum=0.2,
        wind_speed_max=14.0,
        weather_code=1,
        weather_description="Mainly clear",
    )
    db_session.add_all([daily1, daily2])
    db_session.commit()

    # READ
    fetched = db_session.query(WeatherRecord).filter(WeatherRecord.id == record.id).first()
    assert fetched is not None
    assert fetched.location_name == "Tokyo"
    assert len(fetched.daily_records) == 2
    assert fetched.daily_records[0].temp_max == 16.5
    assert fetched.daily_records[1].weather_description == "Mainly clear"


def test_update_weather_record(db_session: Session):
    # Setup initial record
    record = WeatherRecord(
        location_query="London",
        location_name="London",
        latitude=51.5074,
        longitude=-0.1278,
        country="United Kingdom",
        date_start=date(2026, 4, 1),
        date_end=date(2026, 4, 2),
        weather_data=json.dumps({}),
    )
    db_session.add(record)
    db_session.commit()

    # UPDATE
    record.location_name = "Greater London"
    record.date_end = date(2026, 4, 5)
    db_session.commit()

    # Verify update
    updated = db_session.query(WeatherRecord).filter(WeatherRecord.id == record.id).first()
    assert updated.location_name == "Greater London"
    assert updated.date_end == date(2026, 4, 5)


def test_cascade_delete_weather_record(db_session: Session):
    # Setup record with children
    record = WeatherRecord(
        location_query="Berlin",
        location_name="Berlin",
        latitude=52.5200,
        longitude=13.4050,
        country="Germany",
        date_start=date(2026, 5, 1),
        date_end=date(2026, 5, 2),
        weather_data=json.dumps({}),
    )
    db_session.add(record)
    db_session.flush()

    daily = DailyWeatherRecord(
        record_id=record.id,
        date=date(2026, 5, 1),
        temp_max=20.0,
        temp_min=10.0,
    )
    db_session.add(daily)
    db_session.commit()

    rec_id = record.id
    daily_id = daily.id

    # Verify existing before delete
    assert db_session.query(WeatherRecord).filter(WeatherRecord.id == rec_id).count() == 1
    assert db_session.query(DailyWeatherRecord).filter(DailyWeatherRecord.id == daily_id).count() == 1

    # DELETE parent
    db_session.delete(record)
    db_session.commit()

    # Verify parent AND child were cascaded and deleted
    assert db_session.query(WeatherRecord).filter(WeatherRecord.id == rec_id).count() == 0
    assert db_session.query(DailyWeatherRecord).filter(DailyWeatherRecord.id == daily_id).count() == 0


def test_read_invalid_record_id(db_session: Session):
    rec = db_session.query(WeatherRecord).filter(WeatherRecord.id == 999999).first()
    assert rec is None

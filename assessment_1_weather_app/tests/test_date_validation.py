"""Tests for date bounds validation and search schema rules."""

from datetime import date, timedelta
import pytest
from pydantic import ValidationError
from backend.schemas import WeatherSearchRequest, WeatherRecordUpdateRequest


def test_valid_date_range():
    req = WeatherSearchRequest(
        location="Paris",
        date_start=date(2026, 1, 1),
        date_end=date(2026, 1, 10),
    )
    assert req.location == "Paris"
    assert req.date_start == date(2026, 1, 1)
    assert req.date_end == date(2026, 1, 10)


def test_start_date_exceeds_end_date():
    with pytest.raises(ValidationError) as exc:
        WeatherSearchRequest(
            location="Paris",
            date_start=date(2026, 5, 20),
            date_end=date(2026, 5, 10),
        )
    assert "Start date cannot be after end date" in str(exc.value)


def test_date_earlier_than_1940_rejected():
    with pytest.raises(ValidationError) as exc:
        WeatherSearchRequest(
            location="Paris",
            date_start=date(1935, 1, 1),
            date_end=date(1935, 1, 10),
        )
    assert "Start date cannot be earlier than 1940-01-01" in str(exc.value)


def test_date_exceeding_16_day_forecast_limit_rejected():
    future_limit = date.today() + timedelta(days=25)
    with pytest.raises(ValidationError) as exc:
        WeatherSearchRequest(
            location="Paris",
            date_start=date.today(),
            date_end=future_limit,
        )
    assert "max 16-day forecast limit" in str(exc.value)


def test_update_request_date_validation():
    # Valid update
    up = WeatherRecordUpdateRequest(
        date_start=date(2026, 2, 1),
        date_end=date(2026, 2, 5),
    )
    assert up.date_start < up.date_end

    # Inverted date update
    with pytest.raises(ValidationError) as exc:
        WeatherRecordUpdateRequest(
            date_start=date(2026, 2, 10),
            date_end=date(2026, 2, 5),
        )
    assert "Start date cannot be after end date" in str(exc.value)

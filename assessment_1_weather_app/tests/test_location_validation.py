"""Tests for location parsing, coordinates extraction, and geocoding validation."""

import pytest
from backend.services.geocoding import parse_coordinates, geocode_location


def test_parse_valid_coordinates():
    # Valid decimal pairs
    res1 = parse_coordinates("40.7128, -74.0060")
    assert res1 is not None
    assert pytest.approx(res1[0]) == 40.7128
    assert pytest.approx(res1[1]) == -74.0060

    res2 = parse_coordinates("-33.8688,151.2093")
    assert res2 is not None
    assert pytest.approx(res2[0]) == -33.8688
    assert pytest.approx(res2[1]) == 151.2093


def test_parse_invalid_coordinates():
    # Out of range latitude (> 90)
    assert parse_coordinates("105.123, 45.0") is None
    # Out of range longitude (> 180)
    assert parse_coordinates("45.0, 195.0") is None
    # Non-coordinate text
    assert parse_coordinates("London") is None
    assert parse_coordinates("New York, NY") is None


def test_empty_location_raises_value_error():
    with pytest.raises(ValueError, match="Location query cannot be empty"):
        geocode_location("")

    with pytest.raises(ValueError, match="Location query cannot be empty"):
        geocode_location("   ")

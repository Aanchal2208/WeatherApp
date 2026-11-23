"""Tests for weather domain logic, WMO code interpretations, and recommendations."""

from backend.services.weather import get_wmo_info, generate_recommendations


def test_wmo_code_resolution():
    desc, icon = get_wmo_info(0)
    assert desc == "Clear sky"
    assert icon == "☀️"

    desc, icon = get_wmo_info(63)
    assert desc == "Moderate rain"
    assert icon == "🌧️"

    desc, icon = get_wmo_info(95)
    assert desc == "Thunderstorm"

    desc, icon = get_wmo_info(9999)
    assert desc == "Unknown"
    assert icon == "❓"


def test_recommendations_rain():
    rec = generate_recommendations(
        temperature=15.0,
        weather_code=61,  # Slight rain
        wind_speed=10.0,
        precipitation=4.5,
    )
    assert "Indoor activities" in rec["activity_type"]
    assert "umbrella" in rec["advice"].lower()


def test_recommendations_sunny():
    rec = generate_recommendations(
        temperature=22.0,
        weather_code=0,  # Clear sky
        wind_speed=8.0,
        precipitation=0.0,
    )
    assert "sightseeing" in rec["activity_type"].lower()
    assert "layers" in rec["clothing"].lower() or "t-shirt" in rec["clothing"].lower()


def test_recommendations_extreme_cold():
    rec = generate_recommendations(
        temperature=-5.0,
        weather_code=71,  # Slight snow
        wind_speed=15.0,
        precipitation=1.0,
    )
    assert "heavy winter coat" in rec["clothing"].lower()
    assert "cold chill" in rec["precautions"].lower()


def test_recommendations_high_wind():
    rec = generate_recommendations(
        temperature=20.0,
        weather_code=2,  # Partly cloudy
        wind_speed=40.0,  # High wind
        precipitation=0.0,
    )
    assert "High wind warning" in rec["precautions"]

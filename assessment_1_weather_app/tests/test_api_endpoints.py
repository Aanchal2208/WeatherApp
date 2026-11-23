"""API Integration tests for FastAPI endpoints using TestClient."""

from unittest.mock import patch
from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["developer"] == "Aanchal Singh"
    assert "PM Accelerator" in data["organization"]


def test_pm_accelerator_integration_endpoint(client: TestClient):
    resp = client.get("/api/integrations/pm-accelerator")
    assert resp.status_code == 200
    data = resp.json()
    assert "mission" in data
    assert data["developer"] == "Aanchal Singh"
    assert "https://www.pmaccelerator.io/" in data["website"]


def test_youtube_integration_fallback(client: TestClient):
    resp = client.get("/api/integrations/youtube?location=Madrid")
    assert resp.status_code == 200
    data = resp.json()
    assert "search_url" in data
    assert "youtube.com/results" in data["search_url"]
    assert "Madrid" in data["query"]


def test_crud_api_flow(client: TestClient):
    # Mock external geocoding and weather fetch to make unit test deterministic & fast
    mock_geo = {
        "query": "Madrid",
        "total_matches": 1,
        "primary_location": {
            "name": "Madrid",
            "latitude": 40.4168,
            "longitude": -3.7038,
            "country": "Spain",
            "admin1": "Community of Madrid",
            "timezone": "Europe/Madrid",
            "display_name": "Madrid, Spain",
        },
        "all_matches": [],
    }

    mock_weather = {
        "summary": {
            "days_count": 2,
            "overall_temp_max": 25.0,
            "overall_temp_min": 14.0,
            "overall_temp_avg": 19.5,
            "total_precipitation": 0.0,
        },
        "daily_records": [
            {
                "date": "2026-05-01",
                "temp_max": 24.0,
                "temp_min": 14.0,
                "temp_mean": 19.0,
                "apparent_temp_max": 23.5,
                "apparent_temp_min": 13.5,
                "precipitation_sum": 0.0,
                "rain_sum": 0.0,
                "snowfall_sum": 0.0,
                "wind_speed_max": 12.0,
                "weather_code": 0,
                "weather_description": "Clear sky",
                "sunrise": "2026-05-01T06:30",
                "sunset": "2026-05-01T20:30",
            },
            {
                "date": "2026-05-02",
                "temp_max": 25.0,
                "temp_min": 15.0,
                "temp_mean": 20.0,
                "apparent_temp_max": 24.5,
                "apparent_temp_min": 14.5,
                "precipitation_sum": 0.0,
                "rain_sum": 0.0,
                "snowfall_sum": 0.0,
                "wind_speed_max": 10.0,
                "weather_code": 1,
                "weather_description": "Mainly clear",
                "sunrise": "2026-05-02T06:29",
                "sunset": "2026-05-02T20:31",
            },
        ],
    }

    with patch("backend.routes.weather.geocode_location", return_value=mock_geo), \
         patch("backend.routes.weather.fetch_weather_range", return_value=mock_weather):

        # 1. CREATE record via POST /api/weather/search
        create_payload = {
            "location": "Madrid",
            "date_start": "2026-05-01",
            "date_end": "2026-05-02",
        }
        res_create = client.post("/api/weather/search", json=create_payload)
        assert res_create.status_code == 201
        created_data = res_create.json()
        rec_id = created_data["id"]
        assert created_data["location_name"] == "Madrid"
        assert len(created_data["daily_records"]) == 2

        # 2. READ list of records via GET /api/weather/records
        res_list = client.get("/api/weather/records")
        assert res_list.status_code == 200
        list_data = res_list.json()
        assert list_data["total"] >= 1
        assert any(r["id"] == rec_id for r in list_data["items"])

        # 3. READ single record via GET /api/weather/records/{id}
        res_get = client.get(f"/api/weather/records/{rec_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == rec_id

        # 4. UPDATE record via PUT /api/weather/records/{id}
        update_payload = {
            "location": "Madrid",
            "date_start": "2026-05-01",
            "date_end": "2026-05-02",
        }
        res_put = client.put(f"/api/weather/records/{rec_id}", json=update_payload)
        assert res_put.status_code == 200
        assert res_put.json()["id"] == rec_id

        # 5. EXPORT endpoints
        res_csv = client.get(f"/api/export/csv?record_id={rec_id}")
        assert res_csv.status_code == 200
        assert "text/csv" in res_csv.headers["content-type"]
        assert "Madrid" in res_csv.text

        res_json = client.get(f"/api/export/json?record_id={rec_id}")
        assert res_json.status_code == 200
        assert "application/json" in res_json.headers["content-type"]

        res_pdf = client.get(f"/api/export/pdf?record_id={rec_id}")
        assert res_pdf.status_code == 200
        assert "application/pdf" in res_pdf.headers["content-type"]

        # 6. DELETE record via DELETE /api/weather/records/{id}
        res_del = client.delete(f"/api/weather/records/{rec_id}")
        assert res_del.status_code == 200
        assert res_del.json()["success"] is True

        # 7. Verify 404 for deleted record
        res_check = client.get(f"/api/weather/records/{rec_id}")
        assert res_check.status_code == 404


def test_invalid_record_id_returns_404(client: TestClient):
    res = client.get("/api/weather/records/999999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

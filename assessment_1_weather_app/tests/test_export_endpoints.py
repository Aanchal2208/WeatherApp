"""Tests for CSV, JSON, and PDF export generators."""

import json
from backend.services.export import (
    export_records_to_csv,
    export_records_to_json,
    export_records_to_pdf,
)

sample_record = {
    "id": 1,
    "location_query": "Rome",
    "location_name": "Rome",
    "country": "Italy",
    "latitude": 41.9028,
    "longitude": 12.4964,
    "date_start": "2026-06-01",
    "date_end": "2026-06-02",
    "created_at": "2026-06-01T10:00:00",
    "daily_records": [
        {
            "date": "2026-06-01",
            "temp_max": 28.5,
            "temp_min": 18.0,
            "temp_mean": 23.2,
            "precipitation_sum": 0.0,
            "wind_speed_max": 11.2,
            "weather_code": 0,
            "weather_description": "Clear sky",
        }
    ],
}


def test_export_to_csv():
    csv_str = export_records_to_csv([sample_record])
    assert "record_id,location_query,location_name" in csv_str
    assert "Rome" in csv_str
    assert "Italy" in csv_str
    assert "28.5" in csv_str


def test_export_to_json():
    json_str = export_records_to_json([sample_record])
    data = json.loads(json_str)

    assert "metadata" in data
    assert data["metadata"]["developer"] == "Aanchal Singh"
    assert "PM Accelerator" in data["metadata"]["organization"]
    assert len(data["records"]) == 1
    assert data["records"][0]["location_name"] == "Rome"


def test_export_to_pdf():
    pdf_bytes = export_records_to_pdf([sample_record])
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500  # Non-trivial PDF binary
    assert pdf_bytes.startswith(b"%PDF")  # Valid PDF header magic bytes

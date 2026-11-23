# 🌦️ Assessment 1: Weather Application (Backend Engineering)

**Developer:** Aanchal Singh  
**Organization:** PM Accelerator (Product Manager Accelerator)  
**Program:** [PM Accelerator](https://www.pmaccelerator.io/) &bull; [LinkedIn](https://www.linkedin.com/company/product-manager-accelerator/)

---

## 📋 Overview

Assessment 1 is a production-grade weather telemetry application built using **FastAPI**, **PostgreSQL**, **SQLAlchemy ORM**, **Pydantic v2**, and a clean vanilla JavaScript frontend with **Leaflet.js** and **OpenStreetMap**.

The platform provides live weather conditions, historical and forecast queries, rule-based activity recommendations, YouTube travel guides, interactive mapping, complete database CRUD persistence with relational cascading, and multi-format data exports (CSV, JSON, PDF).

---

## 🏗️ Architecture & Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend Framework** | FastAPI 0.110+ | High-performance asynchronous REST API, OpenAPI/Swagger docs |
| **Database** | PostgreSQL 17 | Relational persistence, constraints, foreign keys, cascade delete |
| **ORM & Data Modeling** | SQLAlchemy 2.0 | Declarative ORM models, connection pooling, schema migrations |
| **Data Validation** | Pydantic v2 | Strict schema validation, boundary enforcement, request parsing |
| **Weather APIs** | Open-Meteo (Archive & Forecast) | Real-world historical & forecast observations without fabricated data |
| **Geocoding & Maps** | Open-Meteo & Nominatim (OSM) / Leaflet | Converting queries, zip codes, and GPS coords to coordinates |
| **Integrations** | YouTube Data API v3 | City guide and tour video recommendations (with fallback URL) |
| **Data Export** | ReportLab & Python CSV/JSON | Downloadable CSV, structured JSON, and executive PDF reports |
| **Testing** | Pytest & FastAPI TestClient | Automated CRUD, validation, export, and API tests |

---

## 🗄️ Database Schema & Relational Design

The database uses a normalized **one-to-many relationship**:

1. **`weather_records` (Parent Table)**
   - `id`: Integer primary key (autoincrement, indexed)
   - `location_query`: User's original search input
   - `location_name`: Geocoded canonical city/place name
   - `latitude`, `longitude`: Decimal coordinates
   - `country`, `timezone`: Geographical metadata
   - `date_start`, `date_end`: Query date range bounds
   - `weather_data`: Complete JSON summary telemetry
   - `created_at`, `updated_at`: Audit timestamps

2. **`daily_weather_records` (Child Table)**
   - `id`: Integer primary key
   - `record_id`: Foreign key referencing `weather_records.id` with `ON DELETE CASCADE`
   - `date`: Observation date
   - `temp_max`, `temp_min`, `temp_mean`: Daily temperature metrics
   - `precipitation_sum`, `wind_speed_max`, `weather_code`, `weather_description`
   - `sunrise`, `sunset`: Astronomical times

---

## 🚀 Quickstart & Execution Instructions

### 1. Configure Environment
Copy `.env.example` to `.env` in the project root:
```powershell
cp .env.example .env
```
Ensure `DATABASE_URL` matches your PostgreSQL configuration:
```ini
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/weather_db
```

### 2. Start PostgreSQL
If using local PostgreSQL:
```powershell
# Verify service is running or start it
net start postgresql-x64-17
```

### 3. Launch Backend Application
```powershell
cd assessment_1_weather_app
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser to:
- **Interactive Web App:** `http://127.0.0.1:8000/`
- **Swagger API Documentation:** `http://127.0.0.1:8000/docs`
- **ReDoc Documentation:** `http://127.0.0.1:8000/redoc`

---

## 🧪 Running Automated Tests

Run the test suite using `pytest`:
```powershell
cd assessment_1_weather_app
python -m pytest tests -v
```

---

## 📦 REST API Endpoints

- `GET /api/weather/current` — Current conditions, air quality, recommendations
- `POST /api/weather/search` — Query date range and save record to PostgreSQL (CREATE)
- `GET /api/weather/records` — List saved records with pagination and filters (READ)
- `GET /api/weather/records/{id}` — Retrieve individual record with daily breakdown (READ)
- `PUT /api/weather/records/{id}` — Update record location/dates and re-fetch weather (UPDATE)
- `DELETE /api/weather/records/{id}` — Remove record and cascade delete daily rows (DELETE)
- `GET /api/locations/geocode` — Location resolution with multiple candidate matches
- `GET /api/integrations/youtube` — Travel guide videos
- `GET /api/integrations/map` — OpenStreetMap Leaflet configuration
- `GET /api/export/csv` — Export records to CSV
- `GET /api/export/json` — Export records to JSON
- `GET /api/export/pdf` — Export executive PDF report
- `GET /api/health` — Application and database health diagnostic

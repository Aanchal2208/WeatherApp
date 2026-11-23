# 🌦️ Weather Intelligence Platform

**Dual Technical Assessments Submission &bull; Product Manager Accelerator**  
**Developer:** Aanchal Singh  
**Organization:** [Product Manager Accelerator](https://www.pmaccelerator.io/) &bull; [Official LinkedIn](https://www.linkedin.com/company/product-manager-accelerator/)  
**Collaborator Invitations for Review:** `community@pmaccelerator.io`, `hr@pmaccelerator.io`  

---

## 🧭 Project Introduction & PM Accelerator Mission

The **Product Manager Accelerator Program** offers certified product-management courses, AI product-management training, and career services for aspiring and experienced product professionals. The PM Accelerator website describes support including career coaching, resume review, interview preparation, and salary negotiation.

The **Weather Intelligence Platform** is a comprehensive, production-grade engineering repository that unifies **two separate, fully independent technical assessments** into a single GitHub-ready project:

1. **Assessment 1: Weather Application (Backend Engineering)**  
   A high-concurrency **FastAPI** web service backed by a real **PostgreSQL 17** relational database with complete CRUD operations, cascading referential integrity, Open-Meteo telemetry, Nominatim geocoding, YouTube travel guides, Leaflet interactive mapping, and multi-format data exports (CSV, JSON, PDF).
2. **Assessment 2: Weather Trend Forecasting (Data Science & Machine Learning)**  
   A rigorous data science pipeline auditing global weather telemetry, implementing multi-method anomaly detection (IQR, Z-Score, Isolation Forest), and benchmarking 7 time-series forecasting models (Naive, Moving Average, Exponential Smoothing, Ridge Autoregression, Random Forest, Gradient Boosting, Weighted Ensemble) using strictly chronological holdout validation without target leakage.

> [!NOTE]
> **Independent Modular Architecture:** Both assessments are completely decoupled. Assessment 1 runs without machine learning dependencies; Assessment 2 runs without requiring an active PostgreSQL database.

---

## 🎥 Video Demonstration (1–2 Minutes)

- **Screen-Sharing Demo URL:** `[Add Your Recorded Loom / YouTube / Drive Link Here]`
- **Demo Speaking Script:** Available at [`submission/demo_script.md`](submission/demo_script.md)
- **Preparation Interview Q&A:** Comprehensive 25+ question guide at [`submission/interview_preparation.md`](submission/interview_preparation.md)

---

## 🏗️ Technology Stack

| Layer | Assessment 1 (Backend Engineering) | Assessment 2 (Data Science & ML) |
|---|---|---|
| **Language** | Python 3.10+ | Python 3.10+ |
| **Framework / Server** | FastAPI, Uvicorn, Starlette | Streamlit (Analytics Dashboard) |
| **Database & ORM** | PostgreSQL 17, SQLAlchemy 2.0, Psycopg 3 | Pandas, NumPy, Scipy |
| **Validation** | Pydantic v2 | Scikit-learn (Ensembles & Isolation Forest) |
| **External APIs** | Open-Meteo, Nominatim (OSM), YouTube v3 | Open-Meteo Archive API (Supplemental Series) |
| **Mapping & UI** | Vanilla HTML5/CSS3, Leaflet.js | Matplotlib 3.8+, Seaborn 0.13+ |
| **Reporting** | ReportLab, Python CSV/JSON | Python-PPTX, ReportLab |
| **Test Framework** | Pytest 9.1+, FastAPI TestClient (25 tests) | Pytest 9.1+ (14 tests) |

---

## 📁 Repository Directory Structure

```
WeatherApp/
├── assessment_1_weather_app/          # TECHNICAL ASSESSMENT 1: BACKEND ENGINEERING
│   ├── backend/
│   │   ├── main.py                    # FastAPI entrypoint, CORS, exception handlers
│   │   ├── database.py                # SQLAlchemy engine, session maker, health check
│   │   ├── models.py                  # PostgreSQL ORM models (Parent & Cascade Child)
│   │   ├── schemas.py                 # Pydantic v2 validation models
│   │   ├── config.py                  # Environment settings & constants
│   │   ├── routes/                    # REST API route controllers
│   │   │   ├── weather.py             # CRUD endpoints (/api/weather/*)
│   │   │   ├── locations.py           # Geocoding endpoints (/api/locations/*)
│   │   │   ├── integrations.py        # YouTube & map metadata endpoints
│   │   │   ├── exports.py             # CSV, JSON, PDF export endpoints
│   │   │   └── health.py              # Application diagnostic endpoint
│   │   └── services/                  # Business logic services
│   │       ├── geocoding.py           # Open-Meteo & Nominatim OSM geocoding
│   │       ├── weather.py             # Forecast & Archive API client + rules
│   │       ├── integrations.py        # YouTube API & PM Accelerator info
│   │       └── export.py              # CSV, JSON, and ReportLab PDF generators
│   ├── frontend/                      # Clean vanilla UI
│   │   ├── index.html                 # Single-page dashboard
│   │   ├── css/style.css              # Calm modern responsive CSS
│   │   └── js/app.js                  # Frontend controller communicating with API
│   ├── database/                      # Schema migration scripts & helpers
│   ├── tests/                         # 25 automated Pytest unit/integration tests
│   ├── requirements.txt               # Assessment 1 dependencies
│   └── README.md                      # Assessment 1 documentation
│
├── assessment_2_weather_forecasting/  # TECHNICAL ASSESSMENT 2: DATA SCIENCE & ML
│   ├── data/
│   │   ├── raw/                       # Original Kaggle Global Weather Repository CSV
│   │   ├── processed/                 # Cleaned dataset (weather_cleaned.csv)
│   │   └── external/                  # Multi-continent historical observations
│   ├── notebooks/                     # 7 standard sequential Jupyter notebooks
│   │   ├── 01_data_understanding.ipynb
│   │   ├── 02_data_cleaning.ipynb
│   │   ├── 03_exploratory_analysis.ipynb
│   │   ├── 04_anomaly_detection.ipynb
│   │   ├── 05_forecasting_models.ipynb
│   │   ├── 06_advanced_analysis.ipynb
│   │   └── 07_model_evaluation.ipynb
│   ├── src/                           # Modular reusable Python modules
│   │   ├── data_loader.py             # Dataset loader & time-series depth audit
│   │   ├── preprocessing.py           # Imputation, parsing, lag engineering
│   │   ├── eda.py                     # Statistics & visualization generators
│   │   ├── anomaly_detection.py       # IQR, Z-Score, Isolation Forest
│   │   ├── forecasting.py             # Naive, MA, ExpSmooth, Ridge, RF, GradBoost
│   │   ├── evaluation.py              # MAE, RMSE, R², MAPE, residual plots
│   │   ├── climate_analysis.py        # Climatology & seasonal distributions
│   │   ├── air_quality.py             # Particulate dispersion interactions
│   │   ├── spatial_analysis.py        # Coordinates scatter & continental bars
│   │   └── feature_importance.py      # MDI & permutation importances
│   ├── outputs/
│   │   ├── graphs/                    # 15 publication-ready PNG figures
│   │   └── metrics/                   # model_comparison.csv benchmark results
│   ├── dashboard/
│   │   └── app.py                     # Interactive Streamlit analytics dashboard
│   ├── tests/                         # 14 automated Pytest unit tests
│   ├── run_pipeline.py                # Automated master execution pipeline
│   ├── requirements.txt               # Assessment 2 dependencies
│   └── README.md                      # Assessment 2 documentation
│
├── submission/                        # EXECUTIVE DELIVERABLES
│   ├── presentation/
│   │   └── Weather_Intelligence_Platform.pptx  # 16:9 widescreen presentation
│   ├── reports/
│   │   ├── Weather_App_Technical_Report.pdf    # Assessment 1 technical report
│   │   └── Weather_Forecasting_Report.pdf      # Assessment 2 data science report
│   ├── demo_script.md                 # 1–2 minute screen recording script & sequence
│   └── interview_preparation.md       # 25+ technical interview questions & concepts
│
├── .gitignore                         # Comprehensive ignore list (no secrets/caches)
├── .env.example                       # Environment configuration template
├── requirements.txt                   # Root dependency manifest
└── README.md                          # Master documentation (this file)
```

---

## ⚡ Installation & Quickstart Setup

### 1. Clone & Set Up Environment
```powershell
git clone <YOUR_REPOSITORY_URL> WeatherApp
cd WeatherApp
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Default connection string connects to local PostgreSQL:
```ini
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/weather_db
```

---

## 🚀 Running Assessment 1: Weather Application

### 1. Ensure PostgreSQL is Running
```powershell
# Windows service
net start postgresql-x64-17
```

### 2. Launch FastAPI Web Application
```powershell
cd assessment_1_weather_app
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Access the application in your browser:
- **Interactive Web Dashboard:** `http://127.0.0.1:8000/`
- **Interactive OpenAPI Docs (Swagger UI):** `http://127.0.0.1:8000/docs`
- **ReDoc API Specifications:** `http://127.0.0.1:8000/redoc`

### 3. Run Automated Tests for Assessment 1
```powershell
cd assessment_1_weather_app
python -m pytest tests -v
```
*Result: 25 / 25 tests pass.*

---

## 🔮 Running Assessment 2: Weather Trend Forecasting

### 1. Dataset Acquisition
- **Kaggle Dataset:** [Global Weather Repository on Kaggle](https://www.kaggle.com/datasets/nelgiriyewithana/global-weather-repository)
- Place `Global Weather Repository.csv` in `assessment_2_weather_forecasting/data/raw/`.
- If the Kaggle file is not present, the system automatically uses verified real historical observations from the Open-Meteo Archive API across global reference cities in `data/external/`.

### 2. Run Full Data Science Pipeline
Executes preprocessing, anomaly detection, forecasting models, and generates all 15 figures:
```powershell
cd assessment_2_weather_forecasting
python run_pipeline.py
```

### 3. Launch Interactive Streamlit Dashboard
```powershell
cd assessment_2_weather_forecasting
streamlit run dashboard/app.py
```
Access the dashboard at `http://localhost:8501`.

### 4. Run Automated Tests for Assessment 2
```powershell
cd assessment_2_weather_forecasting
python -m pytest tests -v
```
*Result: 14 / 14 tests pass.*

---

## 📊 Assessment 2 Forecasting Benchmark Results

Evaluated chronologically on an 80/20 train/test split:

| Model Architecture | MAE (°C) | MSE (°C²) | RMSE (°C) | R² Score | MAPE (%) |
|---|---|---|---|---|---|
| **Ridge Autoregression** | **1.464** | **4.384** | **2.094** | **0.9318** | **22.85%** |
| **Gradient Boosting** | 1.516 | 4.506 | 2.123 | 0.9298 | 21.39% |
| **Random Forest** | 1.527 | 4.617 | 2.149 | 0.9281 | 22.39% |
| **Naive Baseline ($y_{t-1}$)** | 1.547 | 5.062 | 2.250 | 0.9212 | 24.07% |
| **Weighted Ensemble** | 2.066 | 6.751 | 2.598 | 0.8949 | 33.65% |
| **Moving Average (7-Day)** | 2.007 | 8.036 | 2.835 | 0.8749 | 37.91% |
| **Exponential Smoothing** | 7.652 | 80.535 | 8.974 | -0.2538 | 126.51% |

> [!TIP]
> **Scientific Integrity:** The Weighted Ensemble achieved an MAE of 2.066°C, slightly below pure Ridge Autoregression (1.464°C) due to Exponential Smoothing variance. This is reported honestly without fabricating false gains.

---

## 📄 Deliverables Summary

1. **Executive PDF Reports:**
   - [`submission/reports/Weather_App_Technical_Report.pdf`](submission/reports/Weather_App_Technical_Report.pdf)
   - [`submission/reports/Weather_Forecasting_Report.pdf`](submission/reports/Weather_Forecasting_Report.pdf)
2. **PowerPoint Presentation:**
   - [`submission/presentation/Weather_Intelligence_Platform.pptx`](submission/presentation/Weather_Intelligence_Platform.pptx)
3. **Demo Video Script & Checklist:**
   - [`submission/demo_script.md`](submission/demo_script.md)
4. **Technical Interview Preparation Guide (25+ Q&A):**
   - [`submission/interview_preparation.md`](submission/interview_preparation.md)

---

## 🔒 Security, Compliance & Attribution
- **No Secrets Exposed:** Passwords, API tokens, and local paths are excluded via `.gitignore` and `.env.example`.
- **Licensing & Attribution:** Open-Meteo data is attributed under the [Non-Commercial Open License / CC BY 4.0](https://open-meteo.com/). Map tiles are attributed to OpenStreetMap contributors.
- **Repository Access:** Ensure the GitHub repository is public or grant read access to `community@pmaccelerator.io` and `hr@pmaccelerator.io`.

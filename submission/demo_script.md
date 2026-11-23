# 🎬 Weather Intelligence Platform: 1–2 Minute Screen-Sharing Demo Script

**Developer:** Aanchal Singh  
**Project:** Weather Intelligence Platform  
**Program:** PM Accelerator (Product Manager Accelerator)  
**Target Duration:** ~90–110 Seconds (1.5 to 2 Minutes)  

---

## 📋 Pre-Recording Setup Checklist
Before starting your screen recording:
1. [ ] **Backend Running:** In terminal 1:
   ```powershell
   cd assessment_1_weather_app
   python -m uvicorn backend.main:app --port 8000
   ```
2. [ ] **Forecasting Dashboard Running:** In terminal 2:
   ```powershell
   cd assessment_2_weather_forecasting
   streamlit run dashboard/app.py
   ```
3. [ ] **Browser Tabs Ready:**
   - Tab 1: `http://localhost:8000/` (Weather Web App)
   - Tab 2: `http://localhost:8501/` (Streamlit Forecasting Dashboard)
   - Tab 3: Terminal window showing passing test output (`pytest`)

---

## ⏱️ Screen-Sharing Sequence & Spoken Script

### [0:00 – 0:15] Introduction & PM Accelerator Mission
- **Screen:** Show Tab 1 (`http://localhost:8000/`) at the top navigation banner.
- **Spoken Words:**  
  > *"Hello! My name is Aanchal Singh, and this is my technical submission for the Product Manager Accelerator program — the Weather Intelligence Platform. PM Accelerator empowers aspiring and advancing technical leaders to master systems design and high-impact engineering. Today I'm demonstrating two complete, independent assessments in one production-ready project: a FastAPI and PostgreSQL weather application, and a machine learning weather forecasting engine."*

---

### [0:15 – 0:45] Assessment 1: Weather Application & PostgreSQL CRUD
- **Screen Action 1:** In the "Current Weather" search bar, type `Tokyo` and click **"Check Weather"**.
- **Spoken Words:**  
  > *"First, in Assessment 1, our FastAPI backend handles live meteorological telemetry. When I search for 'Tokyo', the system geocodes the location, queries Open-Meteo, updates our interactive Leaflet map, displays real-time temperature, humidity, air quality index, and provides explainable activity recommendations."*
- **Screen Action 2:** Scroll down to the **"Range Search"** form. Type `Tokyo`, select a 5-day range, and click **"Fetch & Save Record"**.
- **Spoken Words:**  
  > *"Next is our complete PostgreSQL CRUD engine. When I submit this historical date range, the backend queries the Open-Meteo Archive API and executes a CREATE operation in PostgreSQL, storing parent search metadata and normalized child daily records."*
- **Screen Action 3:** Scroll to the **"Saved Records"** table. Click the **Edit** icon on a record, change the date, click **Save**, and point to the updated table.
- **Spoken Words:**  
  > *"In our Saved Records table, we can paginate, search, edit in-place with our UPDATE endpoint, or trigger cascading deletion with referential integrity. We can also export full database records in CSV, JSON, or an executive PDF report with PM Accelerator branding."*

---

### [0:45 – 1:20] Assessment 2: Weather Trend Forecasting Dashboard
- **Screen Action:** Switch to Tab 2 (`http://localhost:8501/` — Streamlit Dashboard).
- **Spoken Words:**  
  > *"Now moving to Assessment 2: our Weather Trend Forecasting engine. We audited global weather telemetry across 2,928 multi-continent observations. To maintain strict scientific honesty, we used chronological train/test splitting without random shuffling to prevent data leakage."*
- **Screen Action 2:** Click on **"🔍 Anomaly Detection"** in the sidebar. Show Figure 6 (IQR vs Z-score vs Isolation Forest).
- **Spoken Words:**  
  > *"Our pipeline benchmarks three anomaly detection frameworks: Tukey's IQR, Z-Score, and multi-dimensional Isolation Forest, distinguishing between sensor errors and genuine physical extreme events."*
- **Screen Action 3:** Click on **"🔮 Time-Series Forecasting"** and **"🏆 Model Benchmarking"**. Show Figure 7 (Actual vs Predicted) and the metrics table.
- **Spoken Words:**  
  > *"For forecasting, we trained 7 models including Naive and Moving Average baselines, Exponential Smoothing, Ridge Autoregression, Random Forest, Gradient Boosting, and a Weighted Ensemble. Ridge Autoregression and Gradient Boosting delivered the best performance with an MAE of 1.46 degrees Celsius and an R-squared of 0.93."*

---

### [1:20 – 1:40] Verification & Closing Statement
- **Screen Action:** Switch briefly to the terminal showing:
  `25 passed in assessment_1_weather_app` and `14 passed in assessment_2_weather_forecasting`.
- **Spoken Words:**  
  > *"Both assessments are fully verified with 39 automated Pytest cases, comprehensive technical reports, and an interview preparation guide. Thank you to the PM Accelerator team for this opportunity, and I look forward to discussing the technical architecture in my interview!"*

---

## 📌 Video Checklist for Recording
- [x] Clear audio (use a headset or quiet room).
- [x] Display the interactive Leaflet map pin movement.
- [x] Demonstrate at least one CRUD operation (Create, Read, Update, or Delete).
- [x] Show the Streamlit forecasting charts.
- [x] State developer name (**Aanchal Singh**) and organization (**PM Accelerator**).
- [x] Upload video to your personal Google Drive, YouTube (unlisted/public), or Loom, and add the URL to the root `README.md`.

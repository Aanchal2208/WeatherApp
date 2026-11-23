# 🔮 Assessment 2: Weather Trend Forecasting (Data Science & Machine Learning)

**Developer:** Aanchal Singh  
**Organization:** PM Accelerator (Product Manager Accelerator)  
**Program:** [PM Accelerator](https://www.pmaccelerator.io/) &bull; [LinkedIn](https://www.linkedin.com/company/product-manager-accelerator/)

---

## 📋 Overview

Assessment 2 is a rigorous data science and machine learning research platform that analyzes global weather telemetry, conducts automated exploratory data analysis, implements multi-method anomaly detection, and benchmarks seven time-series forecasting models using strictly chronological validation.

---

## 📂 Project Organization

```
assessment_2_weather_forecasting/
├── data/
│   ├── raw/                  # Original Kaggle Global Weather Repository CSV
│   ├── processed/            # Cleaned dataset (weather_cleaned.csv)
│   └── external/             # Verified multi-continent Open-Meteo historical series
├── notebooks/
│   ├── 01_data_understanding.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_exploratory_analysis.ipynb
│   ├── 04_anomaly_detection.ipynb
│   ├── 05_forecasting_models.ipynb
│   ├── 06_advanced_analysis.ipynb
│   └── 07_model_evaluation.ipynb
├── src/
│   ├── data_loader.py        # Dataset acquisition & time series audit
│   ├── preprocessing.py      # Missing values, date parsing, lag features
│   ├── eda.py                # Statistics, distributions, correlation heatmaps
│   ├── anomaly_detection.py  # IQR, Z-Score, Isolation Forest
│   ├── forecasting.py        # Naive, MA, ExpSmoothing, Ridge, RF, GradBoost, Ensemble
│   ├── evaluation.py         # MAE, RMSE, R², MAPE, residuals
│   ├── climate_analysis.py   # Annual climatology & seasonal distributions
│   ├── air_quality.py        # Particulate dispersion interactions
│   ├── spatial_analysis.py   # Global coordinates & continental benchmarks
│   └── feature_importance.py # MDI & permutation importances
├── outputs/
│   ├── graphs/               # 15 publication-ready generated figures
│   └── metrics/              # Model comparison CSV (model_comparison.csv)
├── dashboard/
│   └── app.py                # Interactive Streamlit analytics dashboard
├── tests/                    # Pytest unit tests
├── requirements.txt
└── README.md
```

---

## 📊 Benchmarked Forecasting Models

Models are trained on an 80% chronological train partition and tested on the remaining 20% holdout horizon:

1. **Naive Baseline ($y_{t-1}$):** Predicts previous day's observed temperature.
2. **Moving Average (7-Day):** Rolling 7-day average baseline.
3. **Exponential Smoothing:** Simple adaptive exponential smoothing ($\alpha = 0.35$).
4. **Ridge Autoregression:** Linear regularized regression on multi-lagged temperature features.
5. **Random Forest Regressor:** Non-linear decision tree ensemble with temporal features.
6. **Gradient Boosting Regressor (HistGradientBoosting):** Sequential gradient-boosted decision trees.
7. **Weighted Ensemble:** Explainable weighted average combining Gradient Boosting, Random Forest, and Exponential Smoothing.

### Model Evaluation Results (Test Horizon):
| Model | MAE (°C) | MSE (°C²) | RMSE (°C) | R² Score | MAPE (%) |
|---|---|---|---|---|---|
| **Ridge Autoregression** | **1.464** | **4.384** | **2.094** | **0.9318** | **22.85** |
| **Gradient Boosting** | 1.516 | 4.506 | 2.123 | 0.9298 | 21.39 |
| **Random Forest** | 1.527 | 4.617 | 2.149 | 0.9281 | 22.39 |
| **Naive Baseline (t-1)** | 1.547 | 5.062 | 2.250 | 0.9212 | 24.07 |
| **Weighted Ensemble** | 2.066 | 6.751 | 2.598 | 0.8949 | 33.65 |
| **Moving Average (7-Day)**| 2.007 | 8.036 | 2.835 | 0.8749 | 37.91 |
| **Exponential Smoothing**| 7.652 | 80.535| 8.974 | -0.2538  | 126.51 |

---

## 🚀 Execution Instructions

### 1. Run Complete Data Science Pipeline
Executes data preprocessing, generates all 15 figures, and computes model comparison tables:
```powershell
cd assessment_2_weather_forecasting
python run_pipeline.py
```

### 2. Launch Streamlit Analytics Dashboard
```powershell
cd assessment_2_weather_forecasting
streamlit run dashboard/app.py
```
Open your browser to: `http://localhost:8501`

### 3. Run Automated Tests
```powershell
cd assessment_2_weather_forecasting
python -m pytest tests -v
```

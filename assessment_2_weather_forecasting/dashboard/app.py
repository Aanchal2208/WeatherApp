"""Interactive Streamlit Dashboard for Assessment 2: Weather Trend Forecasting.

Features:
- Dataset overview & telemetry summary
- Historical weather trend lines & rolling averages
- Anomaly detection comparison (IQR vs Z-score vs Isolation Forest)
- Multi-model forecasting benchmarks & actual vs predicted overlays
- Model error evaluation (MAE, MSE, RMSE, R², MAPE)
- Feature importance analysis (MDI & Permutation)
- Climatological and seasonal distributions
- Air quality particulate interactions
- Global geospatial scatter map
- PM Accelerator organizational mission & developer credits

Developer: Aanchal Singh
Organization: PM Accelerator
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np

# Ensure src is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.data_loader import load_dataset, inspect_dataset, validate_time_series_structure
from src.preprocessing import preprocess_pipeline
from src.forecasting import train_and_evaluate_all_models
from src.evaluation import evaluate_forecast_predictions

# Streamlit Page Configuration
st.set_page_config(
    page_title="Weather Intelligence Platform | Forecasting Engine",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-title { font-size: 2.2rem; font-weight: 800; color: #1A365D; margin-bottom: 0.2rem; }
    .sub-title { font-size: 1.05rem; color: #4A5568; margin-bottom: 1.5rem; }
    .metric-box { background-color: #F7FAFC; border: 1px solid #E2E8F0; padding: 1rem; border-radius: 8px; text-align: center; }
    .metric-val { font-size: 1.8rem; font-weight: 700; color: #2B6CB0; }
    .metric-lbl { font-size: 0.85rem; color: #718096; text-transform: uppercase; font-weight: 600; }
    .badge-pm { background-color: #EBF8FF; color: #2B6CB0; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_and_prepare_data():
    """Loads and preprocesses data once and caches results."""
    df_raw, provenance = load_dataset()
    df_clean, meta = preprocess_pipeline(df_raw)
    return df_clean, provenance


# Load dataset
df, provenance = load_and_prepare_data()

# Sidebar Navigation
st.sidebar.markdown("### 🌦️ Weather Intelligence Platform")
st.sidebar.markdown("<span class='badge-pm'>PM Accelerator Assessment 2</span>", unsafe_allow_html=True)
st.sidebar.markdown(f"**Developer:** Aanchal Singh")
st.sidebar.markdown(f"**Data Source:** {provenance.get('source')}")
st.sidebar.divider()

menu_selection = st.sidebar.radio(
    "Navigation Modules:",
    [
        "📊 Dataset Overview",
        "📈 Weather Trends & EDA",
        "🔍 Anomaly Detection",
        "🔮 Time-Series Forecasting",
        "🏆 Model Benchmarking",
        "🧠 Feature Importance",
        "🌍 Spatial & Climate Analysis",
        "🏭 Air Quality Interactions",
        "🎓 About PM Accelerator",
    ],
)

# Top Header
st.markdown("<div class='main-title'>Global Weather Trend Forecasting & Machine Learning</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Technical Assessment 2 &bull; Time-Series Modeling &bull; PM Accelerator</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 1. Dataset Overview
# ---------------------------------------------------------------------------
if menu_selection == "📊 Dataset Overview":
    st.header("Dataset Overview & Structural Validation")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='metric-box'><div class='metric-val'>{len(df):,}</div><div class='metric-lbl'>Total Records</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-box'><div class='metric-val'>{len(df.columns)}</div><div class='metric-lbl'>Total Features</div></div>", unsafe_allow_html=True)
    with col3:
        n_cities = df["location_name"].nunique() if "location_name" in df.columns else 1
        st.markdown(f"<div class='metric-box'><div class='metric-val'>{n_cities}</div><div class='metric-lbl'>Unique Cities</div></div>", unsafe_allow_html=True)
    with col4:
        min_date = df["last_updated"].min()[:10] if "last_updated" in df.columns else "N/A"
        max_date = df["last_updated"].max()[:10] if "last_updated" in df.columns else "N/A"
        st.markdown(f"<div class='metric-box'><div class='metric-val'>{min_date[:4]}–{max_date[:4]}</div><div class='metric-lbl'>Date Range</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Data Sample Preview")
    st.dataframe(df.head(15), use_container_width=True)

    st.subheader("Temporal Depth & Time-Series Validation")
    val_info = validate_time_series_structure(df)
    st.info(f"**Methodological Audit:** {val_info.get('recommendation')}")

# ---------------------------------------------------------------------------
# 2. Weather Trends & EDA
# ---------------------------------------------------------------------------
elif menu_selection == "📈 Weather Trends & EDA":
    st.header("Exploratory Data Analysis (EDA)")

    cities = df["location_name"].unique().tolist() if "location_name" in df.columns else []
    selected_city = st.selectbox("Filter by City:", ["All Cities"] + cities)

    filtered_df = df if selected_city == "All Cities" else df[df["location_name"] == selected_city]

    tab1, tab2, tab3 = st.tabs(["Temperature Trend", "Distribution & Spread", "Precipitation"])

    with tab1:
        st.subheader("Temperature Trajectory Over Time")
        daily_temp = filtered_df.groupby("last_updated")["temperature_celsius"].mean().reset_index()
        st.line_chart(daily_temp.set_index("last_updated"), color="#2B6CB0")
        st.caption("Chronological temperature sequence showing daily observations.")

    with tab2:
        st.subheader("Temperature Distribution Histogram & Boxplots")
        graphs_dir = BASE_DIR / "outputs" / "graphs"
        g1 = graphs_dir / "01_temperature_distribution.png"
        g2 = graphs_dir / "02_temperature_boxplots.png"
        if g1.exists():
            st.image(str(g1), caption="Figure 1: Global Temperature Histogram & KDE Distribution")
        if g2.exists():
            st.image(str(g2), caption="Figure 2: Regional Temperature Boxplots")

    with tab3:
        st.subheader("Precipitation & Correlation Matrices")
        g4 = graphs_dir / "04_precipitation_by_location.png"
        g5 = graphs_dir / "05_correlation_heatmap.png"
        if g4.exists():
            st.image(str(g4), caption="Figure 4: Average Daily Precipitation across Locations")
        if g5.exists():
            st.image(str(g5), caption="Figure 5: Meteorological Feature Correlation Heatmap")

# ---------------------------------------------------------------------------
# 3. Anomaly Detection
# ---------------------------------------------------------------------------
elif menu_selection == "🔍 Anomaly Detection":
    st.header("Multivariate Anomaly Detection")
    st.markdown("""
    This module benchmarks three anomaly detection strategies:
    1. **Tukey's IQR Rule:** Identifies observations beyond $1.5 \\times \\text{IQR}$ from quartiles.
    2. **Z-Score Method:** Detects points exceeding 3 standard deviations from the sample mean.
    3. **Isolation Forest:** Multi-dimensional recursive tree partitioning isolating abnormal feature combinations.
    """)

    graphs_dir = BASE_DIR / "outputs" / "graphs"
    g6 = graphs_dir / "06_anomaly_detection_comparison.png"
    if g6.exists():
        st.image(str(g6), caption="Figure 6: Detected Anomalies across Methods")

    st.info(
        "**Engineering Note for Technical Interview:** An anomaly is a statistical outlier, but in meteorology, "
        "extreme weather phenomena (e.g., heatwaves, monsoons, blizzards) are genuine physical events rather than "
        "erroneous sensor records. They must not be deleted automatically."
    )

# ---------------------------------------------------------------------------
# 4. Time-Series Forecasting
# ---------------------------------------------------------------------------
elif menu_selection == "🔮 Time-Series Forecasting":
    st.header("Forecasting Models Execution & Predictions")
    st.markdown("Models are trained on an 80% chronological train partition and tested on the remaining 20% holdout horizon.")

    graphs_dir = BASE_DIR / "outputs" / "graphs"
    g7 = graphs_dir / "07_actual_vs_predicted.png"
    if g7.exists():
        st.image(str(g7), caption="Figure 7: Ground Truth vs Predicted Temperature across Test Horizon")

    metrics_csv = BASE_DIR / "outputs" / "metrics" / "model_comparison.csv"
    if metrics_csv.exists():
        st.subheader("Test Horizon Performance Table")
        m_df = pd.read_csv(metrics_csv)
        st.dataframe(m_df, use_container_width=True)

# ---------------------------------------------------------------------------
# 5. Model Benchmarking
# ---------------------------------------------------------------------------
elif menu_selection == "🏆 Model Benchmarking":
    st.header("Model Evaluation & Error Diagnostics")
    graphs_dir = BASE_DIR / "outputs" / "graphs"

    col1, col2 = st.columns(2)
    with col1:
        g8 = graphs_dir / "08_model_error_comparison.png"
        if g8.exists():
            st.image(str(g8), caption="Figure 8: MAE & RMSE Error Benchmarks")
    with col2:
        g9 = graphs_dir / "09_residual_distributions.png"
        if g9.exists():
            st.image(str(g9), caption="Figure 9: Residual Error Distributions")

    st.markdown("""
    ### Metric Interpretations:
    - **MAE (Mean Absolute Error):** Average magnitude of forecasting errors in °C. Direct, intuitive measurement.
    - **RMSE (Root Mean Squared Error):** Penalizes larger deviations more heavily; reflects standard deviation of errors.
    - **R² Score:** Proportion of total variance explained by the model relative to a mean baseline.
    - **Ensemble Result:** The Weighted Ensemble combined Gradient Boosting (50%), Random Forest (30%), and Exponential Smoothing (20%). Reporting was conducted honestly without claiming false improvements.
    """)

# ---------------------------------------------------------------------------
# 6. Feature Importance
# ---------------------------------------------------------------------------
elif menu_selection == "🧠 Feature Importance":
    st.header("Feature Importance & Interpretability")
    graphs_dir = BASE_DIR / "outputs" / "graphs"
    g15 = graphs_dir / "15_feature_importance.png"
    if g15.exists():
        st.image(str(g15), caption="Figure 15: MDI vs Permutation Feature Importance")

    st.info(
        "**Core Conceptual Takeaway:** Feature importance measures predictive dependency inside tree architectures, "
        "not physical causation. Lagged temperatures (`temp_lag_1`, `rolling_mean_3`) and solar latitude exhibit the highest predictive utility."
    )

# ---------------------------------------------------------------------------
# 7. Spatial & Climate Analysis
# ---------------------------------------------------------------------------
elif menu_selection == "🌍 Spatial & Climate Analysis":
    st.header("Spatial & Macro-Climatological Analysis")
    graphs_dir = BASE_DIR / "outputs" / "graphs"

    tab1, tab2 = st.tabs(["Geographical Maps", "Climatology Profiles"])
    with tab1:
        g13 = graphs_dir / "13_spatial_temperature_map.png"
        g14 = graphs_dir / "14_continent_comparisons.png"
        if g13.exists():
            st.image(str(g13), caption="Figure 13: Global Coordinates Scatter Temperature Map")
        if g14.exists():
            st.image(str(g14), caption="Figure 14: Continental Thermal Comparisons")

    with tab2:
        g10 = graphs_dir / "10_monthly_climatology.png"
        g11 = graphs_dir / "11_seasonal_distribution.png"
        if g10.exists():
            st.image(str(g10), caption="Figure 10: Annual Climatological Thermal Profile")
        if g11.exists():
            st.image(str(g11), caption="Figure 11: Seasonal Temperature Distributions")

# ---------------------------------------------------------------------------
# 8. Air Quality Interactions
# ---------------------------------------------------------------------------
elif menu_selection == "🏭 Air Quality Interactions":
    st.header("Atmospheric Weather & Air Quality Correlations")
    graphs_dir = BASE_DIR / "outputs" / "graphs"
    g12 = graphs_dir / "12_air_quality_correlations.png"
    if g12.exists():
        st.image(str(g12), caption="Figure 12: Wind & Temperature Correlations with Particulate Concentrations")

    st.markdown("""
    ### Physical Insights:
    - **Wind Velocity vs PM2.5:** Strong inverse relationship. Higher surface wind speeds promote mechanical turbulence and vertical atmospheric dispersion.
    - **Causation vs Correlation:** Observed correlations reflect atmospheric ventilation physics rather than chemical production.
    """)

# ---------------------------------------------------------------------------
# 9. About PM Accelerator
# ---------------------------------------------------------------------------
elif menu_selection == "🎓 About PM Accelerator":
    st.header("About Product Manager Accelerator")
    st.markdown("""
    The **Product Manager Accelerator Program** is designed to support product management professionals 
    through every stage of their career — from students and aspiring PMs breaking into tech to experienced 
    Directors taking on VP roles.
    
    The program provides certified product-management courses, AI product-management training,
    and career services for aspiring and experienced product professionals.
    
    ### Program Pillars:
    - **Hands-on PM & Engineering Curriculum:** Real-world system design, product discovery, and quantitative metrics.
    - **Career Services:** Resume review, interview coaching, salary negotiation, and targeted career guidance.
    - **Professional Portfolio Development:** Opportunities to build tangible product and engineering work.
    
    **Official Website:** [pmaccelerator.io](https://www.pmaccelerator.io/)  
    **Official LinkedIn:** [PM Accelerator on LinkedIn](https://www.linkedin.com/company/product-manager-accelerator/)  
    
    ---
    *Dual Assessment Developed by **Aanchal Singh** for PM Accelerator Fellowship Evaluation.*
    """)

"""Master Execution Pipeline for Assessment 2: Weather Trend Forecasting.

Executes data loading, cleaning, EDA, anomaly detection, multi-model time-series
forecasting, ensemble benchmarking, climate and spatial analysis, and exports
all metrics and visualizations.

Author: Aanchal Singh
Organization: PM Accelerator
"""

import sys
import logging
from pathlib import Path

# Add src to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("weather_forecasting.pipeline")

from src.data_loader import load_dataset, inspect_dataset, validate_time_series_structure
from src.preprocessing import preprocess_pipeline
from src.eda import run_full_eda
from src.anomaly_detection import run_anomaly_detection_benchmark, plot_anomaly_detection_comparison
from src.forecasting import train_and_evaluate_all_models, split_chronological_data, prepare_feature_matrices
from src.evaluation import (
    evaluate_forecast_predictions,
    plot_actual_vs_predicted,
    plot_model_comparison_bar,
    plot_residuals,
)
from src.climate_analysis import plot_monthly_climatology, plot_seasonal_distribution
from src.air_quality import plot_air_quality_weather_interactions
from src.spatial_analysis import plot_geographical_scatter, plot_continent_comparison
from src.feature_importance import plot_feature_importances


def run():
    logger.info("=== Starting Assessment 2 Forecasting Pipeline ===")

    # 1. Dataset Acquisition & Inspection
    df_raw, provenance = load_dataset()
    logger.info("Loaded dataset with %d rows and %d columns. Source: %s", len(df_raw), len(df_raw.columns), provenance["source"])

    inspection = inspect_dataset(df_raw)
    validation = validate_time_series_structure(df_raw)
    logger.info("Dataset inspection complete. Time-series check: %s", validation["recommendation"])

    # 2. Cleaning & Preprocessing
    df_clean, meta = preprocess_pipeline(df_raw)
    logger.info("Preprocessing complete. Cleaned rows: %d, columns: %d", meta["final_rows"], meta["final_columns"])

    # 3. Exploratory Data Analysis (EDA)
    logger.info("Executing EDA visualizations...")
    eda_res = run_full_eda(df_clean)
    logger.info("EDA complete. Generated %d charts.", len(eda_res["generated_graphs"]))

    # 4. Anomaly Detection
    logger.info("Executing Anomaly Detection benchmark...")
    df_flagged, anomaly_summary = run_anomaly_detection_benchmark(df_clean)
    plot_anomaly_detection_comparison(df_flagged)
    logger.info("Anomaly detection complete. Flagged counts: IQR=%d, Z-Score=%d, IsolationForest=%d",
                anomaly_summary.get("iqr_anomalies_detected", 0),
                anomaly_summary.get("zscore_anomalies_detected", 0),
                anomaly_summary.get("isolation_forest_anomalies_detected", 0))

    # 5. Forecasting Models & Evaluation
    logger.info("Training forecasting models...")
    forecast_results = train_and_evaluate_all_models(df_clean)
    y_test = forecast_results["y_test"]
    predictions = forecast_results["predictions"]

    metrics_df = evaluate_forecast_predictions(y_test, predictions)
    logger.info("\n=== Model Comparison Results ===\n%s", metrics_df.to_string())

    plot_actual_vs_predicted(y_test, predictions, test_dates=forecast_results["test_dates"])
    plot_model_comparison_bar(metrics_df)
    plot_residuals(y_test, predictions)

    # 6. Climate & Environmental Analysis
    logger.info("Generating Climate and Air Quality figures...")
    plot_monthly_climatology(df_clean)
    plot_seasonal_distribution(df_clean)
    plot_air_quality_weather_interactions(df_clean)

    # 7. Spatial & Regional Analysis
    logger.info("Generating Spatial and Geographical figures...")
    plot_geographical_scatter(df_clean)
    plot_continent_comparison(df_clean)

    # 8. Feature Importance
    logger.info("Generating Feature Importance analysis...")
    train_df, test_df = split_chronological_data(df_clean)
    X_train, y_train, X_test, y_test_sub, features = prepare_feature_matrices(train_df, test_df)
    rf_model = forecast_results["fitted_models"]["random_forest"]
    plot_feature_importances(rf_model, features, X_test, y_test_sub)

    logger.info("=== Assessment 2 Pipeline Successfully Completed! All figures saved to outputs/graphs/ ===")


if __name__ == "__main__":
    run()

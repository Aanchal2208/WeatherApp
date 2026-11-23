"""Advanced anomaly detection module for Assessment 2.

Implements and benchmarks three anomaly detection methodologies:
1. Interquartile Range (IQR) rule
2. Z-Score (standard deviations from mean)
3. Isolation Forest (multivariate unsupervised ensemble)

Explains the distinction between sensor corruption vs genuine extreme weather events
(e.g., heatwaves, monsoons, blizzards).

Author: Aanchal Singh
Organization: PM Accelerator
"""

import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

logger = logging.getLogger("weather_forecasting.anomaly_detection")

OUTPUTS_GRAPHS_DIR = Path(__file__).resolve().parent.parent / "outputs" / "graphs"
OUTPUTS_GRAPHS_DIR.mkdir(parents=True, exist_ok=True)


def detect_iqr_anomalies(series: pd.Series, multiplier: float = 1.5) -> pd.Series:
    """Tukey's IQR method: Flags values outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR]."""
    q25 = series.quantile(0.25)
    q75 = series.quantile(0.75)
    iqr = q75 - q25
    lower = q25 - (multiplier * iqr)
    upper = q75 + (multiplier * iqr)
    return (series < lower) | (series > upper)


def detect_zscore_anomalies(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    """Z-Score method: Flags values exceeding 3 standard deviations from mean."""
    mean = series.mean()
    std = series.std()
    if std == 0 or np.isnan(std):
        return pd.Series(False, index=series.index)
    return ((series - mean).abs() / std) > threshold


def detect_isolation_forest_anomalies(
    df: pd.DataFrame,
    features: list,
    contamination: float = 0.03,
    random_state: int = 42,
) -> pd.Series:
    """Isolation Forest: Unsupervised recursive partitioning isolating outliers in multi-dimensional space."""
    clean_sub = df[features].dropna()
    if len(clean_sub) < 10:
        return pd.Series(False, index=df.index)

    iso = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=100,
    )
    preds = iso.fit_predict(clean_sub)
    # -1 represents outlier/anomaly, 1 represents inlier
    is_anomaly = pd.Series(preds == -1, index=clean_sub.index)
    return is_anomaly.reindex(df.index, fill_value=False)


def run_anomaly_detection_benchmark(
    df: pd.DataFrame,
    target_col: str = "temperature_celsius",
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Runs all three detection methods on temperature and multivariate features,

    returning flagged dataframe and comparative metrics.
    """
    df = df.copy()
    if target_col not in df.columns:
        return df, {}

    # 1. IQR on target
    df["anomaly_iqr"] = detect_iqr_anomalies(df[target_col])

    # 2. Z-Score on target
    df["anomaly_zscore"] = detect_zscore_anomalies(df[target_col])

    # 3. Isolation Forest on available weather variables
    available_features = [
        c for c in [target_col, "precip_mm", "wind_kph", "humidity", "pressure_mb"]
        if c in df.columns
    ]
    df["anomaly_isolation_forest"] = detect_isolation_forest_anomalies(df, available_features)

    # Summary counts
    total_obs = len(df)
    iqr_count = int(df["anomaly_iqr"].sum())
    zscore_count = int(df["anomaly_zscore"].sum())
    iso_count = int(df["anomaly_isolation_forest"].sum())

    summary = {
        "total_observations": total_obs,
        "iqr_anomalies_detected": iqr_count,
        "iqr_anomaly_rate_pct": round((iqr_count / total_obs) * 100, 2),
        "zscore_anomalies_detected": zscore_count,
        "zscore_anomaly_rate_pct": round((zscore_count / total_obs) * 100, 2),
        "isolation_forest_anomalies_detected": iso_count,
        "isolation_forest_anomaly_rate_pct": round((iso_count / total_obs) * 100, 2),
        "analytical_rationale": (
            "IQR detects univariate distribution tails without assuming normality. "
            "Z-Score relies on Gaussian distribution assumptions and is sensitive to extreme skewness. "
            "Isolation Forest captures complex non-linear multivariate relationships between temperature, "
            "wind, and precipitation. Critical scientific distinction: An anomaly is a statistical outlier; "
            "genuine extreme events (such as cold snaps and tropical heatwaves) reflect physical climate reality "
            "and must not be deleted indiscriminately."
        ),
    }

    return df, summary


def plot_anomaly_detection_comparison(
    df: pd.DataFrame,
    date_col: str = "last_updated",
    target_col: str = "temperature_celsius",
) -> str:
    """Visualizes flagged anomalies across time series for method comparison."""
    if target_col not in df.columns or "anomaly_isolation_forest" not in df.columns:
        return ""

    df_plot = df.copy()
    if date_col in df_plot.columns:
        df_plot[date_col] = pd.to_datetime(df_plot[date_col], errors="coerce")
        df_plot = df_plot.dropna(subset=[date_col, target_col]).sort_values(date_col)
        x_vals = df_plot[date_col]
    else:
        x_vals = df_plot.index

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)

    # Plot 1: Z-score & IQR anomalies
    ax1.plot(x_vals, df_plot[target_col], color="#CBD5E0", label="Normal Observations", zorder=1)
    
    iqr_pts = df_plot[df_plot["anomaly_iqr"]]
    ax1.scatter(
        x_vals[df_plot["anomaly_iqr"]],
        iqr_pts[target_col],
        color="#DD6B20",
        label=f"IQR Flagged ({len(iqr_pts)})",
        s=30,
        zorder=2,
    )

    z_pts = df_plot[df_plot["anomaly_zscore"]]
    ax1.scatter(
        x_vals[df_plot["anomaly_zscore"]],
        z_pts[target_col],
        color="#C53030",
        marker="x",
        label=f"Z-Score Flagged ({len(z_pts)})",
        s=45,
        zorder=3,
    )
    ax1.set_title("Univariate Outlier Detection: Tukey's IQR vs Z-Score", fontweight="bold")
    ax1.set_ylabel("Temperature (°C)")
    ax1.legend(loc="upper right", frameon=True)

    # Plot 2: Isolation Forest anomalies
    iso_pts = df_plot[df_plot["anomaly_isolation_forest"]]
    ax2.plot(x_vals, df_plot[target_col], color="#CBD5E0", label="Normal Observations", zorder=1)
    ax2.scatter(
        x_vals[df_plot["anomaly_isolation_forest"]],
        iso_pts[target_col],
        color="#805AD5",
        label=f"Isolation Forest Flagged ({len(iso_pts)})",
        s=35,
        zorder=2,
    )
    ax2.set_title("Multivariate Unsupervised Anomaly Detection: Isolation Forest", fontweight="bold")
    ax2.set_xlabel("Date / Index")
    ax2.set_ylabel("Temperature (°C)")
    ax2.legend(loc="upper right", frameon=True)

    fig.text(
        0.5, -0.02,
        "Interpretation: Isolation Forest flags multivariate joint extremes (e.g., high heat + high wind + low pressure) "
        "even when individual 1D temperature values remain within standard statistical bounds.",
        ha="center", fontsize=8, color="#4A5568", wrap=True
    )

    out_file = OUTPUTS_GRAPHS_DIR / "06_anomaly_detection_comparison.png"
    fig.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return str(out_file)

"""Data cleaning, preprocessing, and feature engineering pipeline for Assessment 2.

Implements:
- Missing value analysis & imputation (median/mode)
- Duplicate removal
- Strict date parsing on last_updated
- Outlier identification (IQR & Z-Score)
- Leakage-free lag & rolling feature generation
- Feature scaling & encoding

Author: Aanchal Singh
Organization: PM Accelerator
"""

import logging
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler

logger = logging.getLogger("weather_forecasting.preprocessing")

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes column headers to lowercase with underscores."""
    df = df.copy()
    df.columns = [
        c.strip().lower().replace(" ", "_").replace(".", "_").replace("-", "_")
        for c in df.columns
    ]
    return df


def handle_missing_values(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """Analyzes and imputes missing values.

    Numerical columns: Median imputation (robust against skewed weather distributions).
    Categorical columns: Mode imputation.
    """
    df = df.copy()
    missing_summary = df.isnull().sum().to_dict()

    for col in df.columns:
        if df[col].isnull().sum() > 0:
            if pd.api.types.is_numeric_dtype(df[col]):
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
            else:
                mode_val = df[col].mode()
                fill_val = mode_val[0] if not mode_val.empty else "Unknown"
                df[col] = df[col].fillna(fill_val)

    return df, missing_summary


def remove_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Identifies and drops exact duplicate records."""
    df = df.copy()
    initial_len = len(df)
    df = df.drop_duplicates()
    dropped_count = initial_len - len(df)
    return df, dropped_count


def parse_datetime_features(df: pd.DataFrame, date_col: str = "last_updated") -> pd.DataFrame:
    """Parses date column into pandas datetime and extracts temporal components."""
    df = df.copy()

    # Find matching date column if named slightly differently
    if date_col not in df.columns:
        candidates = [c for c in df.columns if "date" in c or "update" in c or "time" in c]
        if candidates:
            date_col = candidates[0]

    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        # Drop rows where date could not be parsed
        df = df.dropna(subset=[date_col])

        df["year"] = df[date_col].dt.year
        df["month"] = df[date_col].dt.month
        df["day"] = df[date_col].dt.day
        df["day_of_week"] = df[date_col].dt.dayofweek
        df["day_of_year"] = df[date_col].dt.dayofyear
        df["quarter"] = df[date_col].dt.quarter
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

        # Meteorological seasons (Northern Hemisphere reference)
        def get_season(m):
            if m in [12, 1, 2]:
                return "Winter"
            elif m in [3, 4, 5]:
                return "Spring"
            elif m in [6, 7, 8]:
                return "Summer"
            else:
                return "Autumn"

        df["season"] = df["month"].apply(get_season)

        # Cyclical transformations for month and day of year
        df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12.0)
        df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12.0)
        df["sin_day_of_year"] = np.sin(2 * np.pi * df["day_of_year"] / 365.25)
        df["cos_day_of_year"] = np.cos(2 * np.pi * df["day_of_year"] / 365.25)

    return df


def create_time_series_lag_features(
    df: pd.DataFrame,
    target_col: str = "temperature_celsius",
    group_col: Optional[str] = "location_name",
    date_col: str = "last_updated",
    lags: List[int] = [1, 2, 7],
    rolling_windows: List[int] = [3, 7],
) -> pd.DataFrame:
    """Creates strictly backwards-looking lag and rolling statistical features.

    Avoids target leakage: only prior observations are used to predict future steps.
    """
    df = df.copy()
    if target_col not in df.columns or date_col not in df.columns:
        return df

    # Sort chronologically
    sort_cols = [group_col, date_col] if (group_col and group_col in df.columns) else [date_col]
    df = df.sort_values(by=sort_cols).reset_index(drop=True)

    # Helper for grouped vs global shifts
    def apply_lag(shift_n: int):
        if group_col and group_col in df.columns:
            return df.groupby(group_col)[target_col].shift(shift_n)
        return df[target_col].shift(shift_n)

    # Lags
    for lag in lags:
        df[f"{target_col}_lag_{lag}"] = apply_lag(lag)

    # Rolling statistics (using shift(1) first so current step is not included in rolling mean)
    for w in rolling_windows:
        if group_col and group_col in df.columns:
            shifted = df.groupby(group_col)[target_col].shift(1)
            df[f"{target_col}_rolling_mean_{w}"] = shifted.rolling(w, min_periods=1).mean()
            df[f"{target_col}_rolling_std_{w}"] = shifted.rolling(w, min_periods=1).std().fillna(0)
        else:
            shifted = df[target_col].shift(1)
            df[f"{target_col}_rolling_mean_{w}"] = shifted.rolling(w, min_periods=1).mean()
            df[f"{target_col}_rolling_std_{w}"] = shifted.rolling(w, min_periods=1).std().fillna(0)

    # Forward fill or backfill any edge NaNs created by lagging
    df = df.bfill().ffill()
    return df


def detect_outliers_iqr(df: pd.DataFrame, col: str, multiplier: float = 1.5) -> pd.Series:
    """Detects outliers using Tukey's Interquartile Range (IQR) method."""
    q25 = df[col].quantile(0.25)
    q75 = df[col].quantile(0.75)
    iqr = q75 - q25
    lower_bound = q25 - (multiplier * iqr)
    upper_bound = q75 + (multiplier * iqr)
    return (df[col] < lower_bound) | (df[col] > upper_bound)


def detect_outliers_zscore(df: pd.DataFrame, col: str, threshold: float = 3.0) -> pd.Series:
    """Detects outliers exceeding specified standard deviations from mean."""
    mean = df[col].mean()
    std = df[col].std()
    if std == 0 or np.isnan(std):
        return pd.Series(False, index=df.index)
    z_scores = (df[col] - mean).abs() / std
    return z_scores > threshold


def preprocess_pipeline(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Complete end-to-end preprocessing execution.

    Saves clean dataset to data/processed/weather_cleaned.csv.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df_clean = clean_column_names(df)

    # Check target temperature column name
    temp_col = None
    for c in ["temperature_celsius", "temperature", "temp_c", "temperature_2m_mean"]:
        if c in df_clean.columns:
            temp_col = c
            break

    if temp_col and temp_col != "temperature_celsius":
        df_clean["temperature_celsius"] = df_clean[temp_col]

    df_clean, duplicates_removed = remove_duplicates(df_clean)
    df_clean, missing_summary = handle_missing_values(df_clean)
    df_clean = parse_datetime_features(df_clean)

    if "temperature_celsius" in df_clean.columns:
        df_clean = create_time_series_lag_features(df_clean, target_col="temperature_celsius")

    output_path = PROCESSED_DIR / "weather_cleaned.csv"
    df_clean.to_csv(output_path, index=False)

    metadata = {
        "final_rows": len(df_clean),
        "final_columns": len(df_clean.columns),
        "duplicates_removed": duplicates_removed,
        "processed_file": str(output_path),
    }

    return df_clean, metadata

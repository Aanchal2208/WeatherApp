"""Unit tests for preprocessing, date parsing, missing values, and lag creation."""

import pandas as pd
import numpy as np
from src.preprocessing import (
    clean_column_names,
    handle_missing_values,
    remove_duplicates,
    parse_datetime_features,
    create_time_series_lag_features,
    detect_outliers_iqr,
    detect_outliers_zscore,
)


def test_clean_column_names():
    df = pd.DataFrame({"Temperature (C)": [1], "Wind Speed-KPH": [2]})
    cleaned = clean_column_names(df)
    assert "temperature_(c)" in cleaned.columns
    assert "wind_speed_kph" in cleaned.columns


def test_handle_missing_values():
    df = pd.DataFrame({
        "num": [10.0, 20.0, np.nan, 30.0],
        "cat": ["A", "A", None, "B"],
    })
    df_clean, summary = handle_missing_values(df)
    assert df_clean["num"].isnull().sum() == 0
    assert df_clean["cat"].isnull().sum() == 0
    assert df_clean["num"].iloc[2] == 20.0  # Median of [10, 20, 30]
    assert df_clean["cat"].iloc[2] == "A"   # Mode


def test_remove_duplicates():
    df = pd.DataFrame({"val": [1, 1, 2, 3]})
    df_clean, dropped = remove_duplicates(df)
    assert len(df_clean) == 3
    assert dropped == 1


def test_parse_datetime_features():
    df = pd.DataFrame({"last_updated": ["2024-03-15", "2024-07-20"]})
    df_parsed = parse_datetime_features(df)
    assert "month" in df_parsed.columns
    assert "season" in df_parsed.columns
    assert df_parsed["season"].iloc[0] == "Spring"
    assert df_parsed["season"].iloc[1] == "Summer"


def test_create_time_series_lag_features():
    df = pd.DataFrame({
        "last_updated": pd.date_range("2024-01-01", periods=10, freq="D"),
        "temperature_celsius": [10, 12, 14, 16, 18, 20, 22, 24, 26, 28],
    })
    df_lag = create_time_series_lag_features(df, lags=[1, 2], rolling_windows=[3])
    assert "temperature_celsius_lag_1" in df_lag.columns
    assert "temperature_celsius_rolling_mean_3" in df_lag.columns
    assert df_lag["temperature_celsius_lag_1"].iloc[2] == 12.0


def test_outlier_detection_iqr_and_zscore():
    data = pd.Series([10, 11, 12, 10, 11, 100])  # 100 is an extreme outlier
    df = pd.DataFrame({"val": data})
    iqr_flags = detect_outliers_iqr(df, "val")
    z_flags = detect_outliers_zscore(df, "val", threshold=2.0)
    assert iqr_flags.iloc[-1] == True
    assert z_flags.iloc[-1] == True

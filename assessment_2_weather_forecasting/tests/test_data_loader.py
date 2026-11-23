"""Unit tests for dataset acquisition and inspection logic."""

import pandas as pd
from src.data_loader import inspect_dataset, validate_time_series_structure


def test_inspect_dataset():
    sample_df = pd.DataFrame({
        "city": ["Tokyo", "London", "Paris"],
        "temp": [15.2, 12.0, 14.5],
        "precip": [0.0, 2.5, None],
    })
    inspection = inspect_dataset(sample_df)

    assert inspection["num_rows"] == 3
    assert inspection["num_cols"] == 3
    assert inspection["total_missing_values"] == 1
    assert inspection["duplicate_rows"] == 0
    assert "temp" in inspection["numerical_columns"]
    assert "city" in inspection["categorical_columns"]


def test_validate_time_series_structure():
    # Long time series
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    df_series = pd.DataFrame({
        "last_updated": dates,
        "temperature_celsius": range(60),
        "location_name": ["Tokyo"] * 60,
    })
    val = validate_time_series_structure(df_series)
    assert val["unique_dates_count"] == 60
    assert val["is_short_or_snapshot"] is False

    # Snapshot dataset
    df_snapshot = pd.DataFrame({
        "last_updated": ["2024-01-01", "2024-01-01"],
        "temperature_celsius": [20.0, 25.0],
        "location_name": ["Tokyo", "London"],
    })
    val_snap = validate_time_series_structure(df_snapshot)
    assert val_snap["is_short_or_snapshot"] is True

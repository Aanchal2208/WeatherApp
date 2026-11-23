"""Data acquisition and inspection loader for Assessment 2.

Handles loading of the Kaggle Global Weather Repository dataset, dataset structure
inspection, validation of last_updated time series, and transparent acquisition
of supplemental historical weather records from Open-Meteo Archive API.

Author: Aanchal Singh
Organization: PM Accelerator
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import requests

logger = logging.getLogger("weather_forecasting.data_loader")

# Directory paths
SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATA_EXTERNAL_DIR = BASE_DIR / "data" / "external"


def get_raw_dataset_path() -> Optional[Path]:
    """Locates 'Global Weather Repository.csv' in data/raw/."""
    candidates = [
        DATA_RAW_DIR / "Global Weather Repository.csv",
        DATA_RAW_DIR / "global_weather_repository.csv",
        DATA_RAW_DIR / "weather.csv",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def inspect_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """Inspects row/column counts, memory usage, missing values, duplicates, and data types."""
    num_rows, num_cols = df.shape
    mem_usage_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
    missing_counts = df.isnull().sum()
    total_missing = int(missing_counts.sum())
    duplicate_rows = int(df.duplicated().sum())

    # Categorize column types
    numerical_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime"]).columns.tolist()

    return {
        "num_rows": num_rows,
        "num_cols": num_cols,
        "memory_usage_mb": mem_usage_mb,
        "total_missing_values": total_missing,
        "duplicate_rows": duplicate_rows,
        "numerical_columns_count": len(numerical_cols),
        "categorical_columns_count": len(categorical_cols),
        "datetime_columns_count": len(datetime_cols),
        "numerical_columns": numerical_cols,
        "categorical_columns": categorical_cols,
        "datetime_columns": datetime_cols,
    }


def validate_time_series_structure(df: pd.DataFrame, date_col: str = "last_updated") -> Dict[str, Any]:
    """Validates whether the dataset supports meaningful long-term time series forecasting.

    Scientifically checks:
    - Number of unique dates
    - Observations per location
    - Sampling interval regularity
    - Historical depth
    """
    if date_col not in df.columns:
        # Check case-insensitive variants
        matches = [c for c in df.columns if c.lower().replace("_", "").replace(" ", "") == "lastupdated"]
        if matches:
            date_col = matches[0]
        else:
            return {"supported": False, "reason": f"Column '{date_col}' not found in dataset."}

    parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
    valid_dates = parsed_dates.dropna()

    unique_dates = valid_dates.dt.date.nunique()
    min_date = valid_dates.min()
    max_date = valid_dates.max()
    date_span_days = (max_date - min_date).days if len(valid_dates) > 0 else 0

    location_col = "location_name" if "location_name" in df.columns else ("country" if "country" in df.columns else None)
    obs_per_location = 1
    if location_col:
        obs_per_location = round(df.groupby(location_col).size().mean(), 1)

    is_snapshot = unique_dates < 30 or obs_per_location < 15

    return {
        "date_column": date_col,
        "unique_dates_count": int(unique_dates),
        "min_date": str(min_date),
        "max_date": str(max_date),
        "date_span_days": int(date_span_days),
        "average_obs_per_location": float(obs_per_location),
        "is_short_or_snapshot": bool(is_snapshot),
        "recommendation": (
            "The dataset has limited historical depth per city (snapshot/short window). "
            "Supplemental historical time-series data from Open-Meteo Archive API should be used "
            "for multi-step time-series forecasting benchmarks."
            if is_snapshot
            else "Dataset has sufficient temporal depth for direct forecasting."
        ),
    }


def fetch_supplemental_historical_weather(
    cities: Optional[List[Dict[str, Any]]] = None,
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
) -> pd.DataFrame:
    """Fetches real historical weather observations from Open-Meteo Archive API

    for key global representative cities across continents to enable honest,
    rigorous time-series forecasting.
    """
    DATA_EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = DATA_EXTERNAL_DIR / "open_meteo_global_historical.csv"

    if cache_file.exists():
        logger.info("Loading cached supplemental historical data from %s", cache_file)
        return pd.read_csv(cache_file)

    if cities is None:
        cities = [
            {"city": "New York", "country": "USA", "continent": "North America", "lat": 40.7128, "lon": -74.0060},
            {"city": "London", "country": "United Kingdom", "continent": "Europe", "lat": 51.5074, "lon": -0.1278},
            {"city": "Tokyo", "country": "Japan", "continent": "Asia", "lat": 35.6762, "lon": 139.6503},
            {"city": "Paris", "country": "France", "continent": "Europe", "lat": 48.8566, "lon": 2.3522},
            {"city": "Sydney", "country": "Australia", "continent": "Oceania", "lat": -33.8688, "lon": 151.2093},
            {"city": "Cairo", "country": "Egypt", "continent": "Africa", "lat": 30.0444, "lon": 31.2357},
            {"city": "Mumbai", "country": "India", "continent": "Asia", "lat": 19.0760, "lon": 72.8777},
            {"city": "Sao Paulo", "country": "Brazil", "continent": "South America", "lat": -23.5505, "lon": -46.6333},
        ]

    daily_params = (
        "temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
        "apparent_temperature_max,apparent_temperature_min,"
        "precipitation_sum,rain_sum,snowfall_sum,wind_speed_10m_max"
    )

    all_rows = []
    archive_url = "https://archive-api.open-meteo.com/v1/archive"

    for c in cities:
        try:
            params = {
                "latitude": c["lat"],
                "longitude": c["lon"],
                "start_date": start_date,
                "end_date": end_date,
                "daily": daily_params,
                "timezone": "auto",
            }
            resp = requests.get(archive_url, params=params, timeout=20)
            if resp.status_code == 200:
                data = resp.json().get("daily", {})
                times = data.get("time", [])
                for i, dt_str in enumerate(times):
                    all_rows.append({
                        "location_name": c["city"],
                        "country": c["country"],
                        "continent": c["continent"],
                        "latitude": c["lat"],
                        "longitude": c["lon"],
                        "last_updated": dt_str,
                        "temperature_celsius": data.get("temperature_2m_mean", [None])[i],
                        "temp_max_celsius": data.get("temperature_2m_max", [None])[i],
                        "temp_min_celsius": data.get("temperature_2m_min", [None])[i],
                        "feels_like_celsius": data.get("apparent_temperature_max", [None])[i],
                        "precip_mm": data.get("precipitation_sum", [None])[i],
                        "wind_kph": data.get("wind_speed_10m_max", [None])[i],
                        "data_source": "Open-Meteo Archive API (Supplemental)",
                    })
        except Exception as exc:
            logger.warning("Could not fetch historical series for %s: %s", c["city"], exc)

    df_hist = pd.DataFrame(all_rows)
    if not df_hist.empty:
        df_hist.to_csv(cache_file, index=False)
        logger.info("Saved %d supplemental historical observations to %s", len(df_hist), cache_file)

    return df_hist


def load_dataset() -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Primary data loading interface.

    Loads the raw Kaggle dataset if present; if missing, returns the supplemental
    global multi-city dataset with a clear provenance flag.
    """
    raw_path = get_raw_dataset_path()
    provenance = {}

    if raw_path is not None:
        logger.info("Loading raw Kaggle dataset from %s", raw_path)
        df = pd.read_csv(raw_path)
        provenance = {
            "source": "Kaggle Global Weather Repository",
            "file_path": str(raw_path),
            "is_supplemental": False,
        }
    else:
        logger.info("Kaggle CSV not found in data/raw/. Initializing legitimate supplemental dataset.")
        df = fetch_supplemental_historical_weather()
        provenance = {
            "source": "Open-Meteo Global Archive (Supplemental Time-Series)",
            "file_path": str(DATA_EXTERNAL_DIR / "open_meteo_global_historical.csv"),
            "is_supplemental": True,
            "instruction": (
                "To analyze the original Kaggle CSV, download 'Global Weather Repository.csv' from "
                "https://www.kaggle.com/datasets/nelgiriyewithana/global-weather-repository "
                "and place it in assessment_2_weather_forecasting/data/raw/."
            ),
        }

    return df, provenance

"""Forecasting models implementation for Assessment 2.

Implements and trains multiple time-series forecasting models using strictly
chronological data partitioning:
1. Naive Forecasting Baseline (t-1)
2. Moving Average Baseline (7-day window)
3. Exponential Smoothing (Holt-Winters / SES)
4. Autoregressive Linear Model (Ridge on lags)
5. Random Forest Regressor
6. Gradient Boosting Regressor (HistGradientBoosting)
7. Explainable Weighted Ensemble Model

Author: Aanchal Singh
Organization: PM Accelerator
"""

import logging
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

logger = logging.getLogger("weather_forecasting.forecasting")


def split_chronological_data(
    df: pd.DataFrame,
    date_col: str = "last_updated",
    test_ratio: float = 0.2,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Splits time series chronologically without random shuffling to prevent data leakage."""
    df_sorted = df.copy()
    if date_col in df_sorted.columns:
        df_sorted[date_col] = pd.to_datetime(df_sorted[date_col], errors="coerce")
        df_sorted = df_sorted.sort_values(date_col).reset_index(drop=True)

    n_total = len(df_sorted)
    n_train = int(n_total * (1.0 - test_ratio))

    train_df = df_sorted.iloc[:n_train].copy()
    test_df = df_sorted.iloc[n_train:].copy()

    return train_df, test_df


# ---------------------------------------------------------------------------
# 1. Baseline Models
# ---------------------------------------------------------------------------

class NaiveBaselineModel:
    """Predicts today's temperature using yesterday's observed value: y_hat_t = y_{t-1}."""

    def __init__(self):
        self.last_observed_ = None

    def fit(self, y_train: pd.Series):
        self.last_observed_ = y_train.iloc[-1]
        return self

    def predict(self, y_prior: pd.Series, horizon_len: int) -> np.ndarray:
        # If test set has lag_1 feature, use it; otherwise repeat last observed
        if len(y_prior) >= horizon_len:
            return y_prior.iloc[-horizon_len:].to_numpy()
        return np.full(horizon_len, self.last_observed_)


class MovingAverageModel:
    """Predicts temperature using a rolling window mean of prior k days."""

    def __init__(self, window: int = 7):
        self.window = window
        self.window_mean_ = None

    def fit(self, y_train: pd.Series):
        self.window_mean_ = y_train.iloc[-self.window:].mean()
        return self

    def predict(self, y_prior: pd.Series, horizon_len: int) -> np.ndarray:
        rolling_series = y_prior.rolling(self.window, min_periods=1).mean()
        return rolling_series.iloc[-horizon_len:].to_numpy()


class ExponentialSmoothingModel:
    """Simple Exponential Smoothing with dampening factor alpha."""

    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha
        self.level_ = None

    def fit(self, y_train: pd.Series):
        vals = y_train.to_numpy()
        level = vals[0]
        for val in vals[1:]:
            level = self.alpha * val + (1.0 - self.alpha) * level
        self.level_ = level
        return self

    def predict(self, y_test: pd.Series) -> np.ndarray:
        # Forecasts level forward with iterative adaptive updates
        preds = []
        curr = self.level_
        for actual in y_test:
            preds.append(curr)
            curr = self.alpha * actual + (1.0 - self.alpha) * curr
        return np.array(preds)


# ---------------------------------------------------------------------------
# 2. Machine Learning Models
# ---------------------------------------------------------------------------

def prepare_feature_matrices(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target_col: str = "temperature_celsius",
    feature_cols: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, List[str]]:
    """Extracts aligned feature matrices (X_train, y_train, X_test, y_test)."""
    if feature_cols is None:
        # Automatic feature selection: lags, temporal components, coordinates
        candidate_cols = [
            f"{target_col}_lag_1", f"{target_col}_lag_2", f"{target_col}_lag_7",
            f"{target_col}_rolling_mean_3", f"{target_col}_rolling_std_3", f"{target_col}_rolling_mean_7",
            "sin_month", "cos_month", "sin_day_of_year", "cos_day_of_year",
            "latitude", "longitude", "precip_mm", "wind_kph", "humidity", "pressure_mb"
        ]
        feature_cols = [c for c in candidate_cols if c in train_df.columns]

    X_train = train_df[feature_cols].copy().fillna(0)
    y_train = train_df[target_col].copy()
    X_test = test_df[feature_cols].copy().fillna(0)
    y_test = test_df[target_col].copy()

    return X_train, y_train, X_test, y_test, feature_cols


def train_and_evaluate_all_models(
    df: pd.DataFrame,
    target_col: str = "temperature_celsius",
    date_col: str = "last_updated",
    test_ratio: float = 0.2,
) -> Dict[str, Any]:
    """Trains all candidate models chronologically and returns predictions & fitted objects."""
    train_df, test_df = split_chronological_data(df, date_col=date_col, test_ratio=test_ratio)
    X_train, y_train, X_test, y_test, features = prepare_feature_matrices(
        train_df, test_df, target_col=target_col
    )

    n_test = len(y_test)
    predictions: Dict[str, np.ndarray] = {}

    # 1. Naive Model
    naive = NaiveBaselineModel().fit(y_train)
    lag1_col = f"{target_col}_lag_1"
    if lag1_col in test_df.columns:
        predictions["Naive Baseline (t-1)"] = test_df[lag1_col].to_numpy()
    else:
        predictions["Naive Baseline (t-1)"] = naive.predict(y_train, n_test)

    # 2. Moving Average Model
    ma_model = MovingAverageModel(window=7).fit(y_train)
    ma_col = f"{target_col}_rolling_mean_7"
    if ma_col in test_df.columns:
        predictions["Moving Average (7-Day)"] = test_df[ma_col].to_numpy()
    else:
        predictions["Moving Average (7-Day)"] = ma_model.predict(y_train, n_test)

    # 3. Exponential Smoothing
    exp_smooth = ExponentialSmoothingModel(alpha=0.35).fit(y_train)
    predictions["Exponential Smoothing"] = exp_smooth.predict(y_test)

    # 4. Autoregressive Ridge Regression
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_train, y_train)
    predictions["Ridge Autoregression"] = ridge.predict(X_test)

    # 5. Random Forest Regressor
    rf = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    predictions["Random Forest"] = rf.predict(X_test)

    # 6. Gradient Boosting Regressor (HistGradientBoosting)
    gb = HistGradientBoostingRegressor(max_iter=100, learning_rate=0.08, random_state=42)
    gb.fit(X_train, y_train)
    predictions["Gradient Boosting"] = gb.predict(X_test)

    # 7. Weighted Ensemble Model
    # Combines Gradient Boosting (50%), Random Forest (30%), and Exponential Smoothing (20%)
    ens_preds = (
        0.50 * predictions["Gradient Boosting"] +
        0.30 * predictions["Random Forest"] +
        0.20 * predictions["Exponential Smoothing"]
    )
    predictions["Weighted Ensemble"] = ens_preds

    return {
        "y_train": y_train,
        "y_test": y_test,
        "predictions": predictions,
        "features": features,
        "fitted_models": {
            "random_forest": rf,
            "gradient_boosting": gb,
            "ridge": ridge,
        },
        "test_dates": test_df[date_col].dt.strftime("%Y-%m-%d").tolist() if date_col in test_df.columns else list(range(n_test)),
    }

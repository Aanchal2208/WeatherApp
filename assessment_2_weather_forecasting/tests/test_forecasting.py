"""Unit tests for chronological splitting and forecasting models."""

import pandas as pd
import numpy as np
from src.forecasting import (
    split_chronological_data,
    NaiveBaselineModel,
    MovingAverageModel,
    ExponentialSmoothingModel,
    train_and_evaluate_all_models,
)


def test_split_chronological_data():
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    df = pd.DataFrame({"last_updated": dates, "temp": range(10)})
    train, test = split_chronological_data(df, date_col="last_updated", test_ratio=0.3)

    assert len(train) == 7
    assert len(test) == 3
    # Check strict chronological order
    assert train["last_updated"].max() < test["last_updated"].min()


def test_naive_baseline_model():
    y_train = pd.Series([10.0, 12.0, 15.0])
    naive = NaiveBaselineModel().fit(y_train)
    preds = naive.predict(y_train, horizon_len=2)
    assert len(preds) == 2
    assert preds[0] == 12.0
    assert preds[1] == 15.0


def test_moving_average_model():
    y_train = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    ma = MovingAverageModel(window=3).fit(y_train)
    preds = ma.predict(y_train, horizon_len=2)
    assert len(preds) == 2
    # Prior 3-period rolling values
    assert preds[1] == (30.0 + 40.0 + 50.0) / 3.0


def test_exponential_smoothing_model():
    y_train = pd.Series([10.0, 10.0, 10.0])
    exp_m = ExponentialSmoothingModel(alpha=0.5).fit(y_train)
    preds = exp_m.predict(pd.Series([10.0, 10.0]))
    assert len(preds) == 2
    assert pytest_approx(preds[0], 10.0)


def pytest_approx(val, expected, tol=1e-2):
    return abs(val - expected) < tol

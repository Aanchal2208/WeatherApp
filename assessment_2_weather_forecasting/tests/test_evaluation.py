"""Unit tests for evaluation metrics (MAE, MSE, RMSE, R2, MAPE)."""

import numpy as np
import pandas as pd
from src.evaluation import calculate_mape, evaluate_forecast_predictions


def test_calculate_mape():
    y_true = np.array([100.0, 200.0])
    y_pred = np.array([110.0, 190.0])
    # Relative errors: 10/100 = 10%, 10/200 = 5% -> Average = 7.5%
    mape = calculate_mape(y_true, y_pred)
    assert abs(mape - 7.5) < 1e-2


def test_evaluate_forecast_predictions():
    y_true = pd.Series([20.0, 22.0, 24.0, 26.0])
    predictions = {
        "Model A": np.array([20.0, 22.0, 24.0, 26.0]),  # Perfect match
        "Model B": np.array([19.0, 21.0, 23.0, 25.0]),  # Shift by 1
    }
    df_metrics = evaluate_forecast_predictions(y_true, predictions)

    assert len(df_metrics) == 2
    assert "Model A" in df_metrics["Model"].values
    # Model A perfect R2 = 1.0, MAE = 0.0
    model_a_row = df_metrics[df_metrics["Model"] == "Model A"].iloc[0]
    assert model_a_row["MAE (°C)"] == 0.0
    assert model_a_row["R² Score"] == 1.0

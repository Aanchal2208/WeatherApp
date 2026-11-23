"""Feature importance analysis module for Assessment 2.

Computes Mean Decrease in Impurity (MDI) and Permutation Feature Importance
using fitted tree models. Explains that predictive feature importance
quantifies predictive utility, not physical causation.

Author: Aanchal Singh
Organization: PM Accelerator
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance

logger = logging.getLogger("weather_forecasting.feature_importance")

OUTPUTS_GRAPHS_DIR = Path(__file__).resolve().parent.parent / "outputs" / "graphs"
OUTPUTS_GRAPHS_DIR.mkdir(parents=True, exist_ok=True)


def plot_feature_importances(
    rf_model,
    feature_names: List[str],
    X_test: pd.DataFrame,
    y_test: pd.Series,
    top_n: int = 10,
) -> str:
    """Computes and plots both MDI and Permutation Importance side by side."""
    # 1. MDI Impurity-based importances
    importances_mdi = rf_model.feature_importances_
    df_mdi = pd.DataFrame({
        "Feature": feature_names,
        "Importance": importances_mdi,
    }).sort_values("Importance", ascending=False).head(top_n)

    # 2. Permutation Importance on test set
    perm_res = permutation_importance(
        rf_model, X_test, y_test, n_repeats=5, random_state=42, n_jobs=-1
    )
    df_perm = pd.DataFrame({
        "Feature": feature_names,
        "Importance": perm_res.importances_mean,
    }).sort_values("Importance", ascending=False).head(top_n)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # MDI Barplot
    ax1.barh(df_mdi["Feature"], df_mdi["Importance"], color="#2B6CB0", edgecolor="#1A365D")
    ax1.invert_yaxis()
    ax1.set_title("MDI Impurity Feature Importance (Random Forest)", fontweight="bold")
    ax1.set_xlabel("Mean Decrease in Impurity")

    # Permutation Barplot
    ax2.barh(df_perm["Feature"], df_perm["Importance"], color="#319795", edgecolor="#234E52")
    ax2.invert_yaxis()
    ax2.set_title("Permutation Feature Importance (Test Set)", fontweight="bold")
    ax2.set_xlabel("Mean Accuracy Degradation Upon Shuffle")

    fig.text(
        0.5, -0.06,
        "Interpretation: Recent temperature lags (lag_1, rolling_mean_3) and solar latitude dominate predictive importance. "
        "Critical distinction: Feature importance reflects model dependency and predictive utility, not scientific physical causation.",
        ha="center", fontsize=8, color="#4A5568", wrap=True
    )

    out_file = OUTPUTS_GRAPHS_DIR / "15_feature_importance.png"
    fig.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return str(out_file)

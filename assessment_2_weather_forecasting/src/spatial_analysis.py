"""Spatial and geographical analysis module for Assessment 2.

Plots coordinates scatter maps and benchmarks climate differences across
continents and global geographic zones.

Author: Aanchal Singh
Organization: PM Accelerator
"""

import logging
from pathlib import Path
from typing import Dict, Any
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

logger = logging.getLogger("weather_forecasting.spatial_analysis")

OUTPUTS_GRAPHS_DIR = Path(__file__).resolve().parent.parent / "outputs" / "graphs"
OUTPUTS_GRAPHS_DIR.mkdir(parents=True, exist_ok=True)


def plot_geographical_scatter(
    df: pd.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    temp_col: str = "temperature_celsius",
) -> str:
    """Generates global coordinates scatter map color-coded by observed temperature."""
    if lat_col not in df.columns or lon_col not in df.columns or temp_col not in df.columns:
        return ""

    fig, ax = plt.subplots(figsize=(11, 5.5))
    sc = ax.scatter(
        df[lon_col],
        df[lat_col],
        c=df[temp_col],
        cmap="coolwarm",
        s=35,
        alpha=0.8,
        edgecolors="none",
    )

    cbar = plt.colorbar(sc, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label("Temperature (°C)")

    ax.set_title("Global Geospatial Weather Telemetry (Coordinates Scatter)", fontweight="bold")
    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)

    # Equator line reference
    ax.axhline(0, color="#718096", linestyle=":", linewidth=1, label="Equator (0°)")
    ax.legend(loc="lower left")

    fig.text(
        0.5, -0.04,
        "Interpretation: Latitude governs the primary thermal gradient. Stations nearest the equator exhibit consistent high warmth, "
        "while high-latitude polar and subpolar stations exhibit lowest temperatures.",
        ha="center", fontsize=8, color="#4A5568", wrap=True
    )

    out_file = OUTPUTS_GRAPHS_DIR / "13_spatial_temperature_map.png"
    fig.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return str(out_file)


def plot_continent_comparison(
    df: pd.DataFrame,
    continent_col: str = "continent",
    temp_col: str = "temperature_celsius",
) -> str:
    """Generates comparison bar chart of mean temperature across continents."""
    # Check if continent column exists, or infer from coordinates / country
    plot_df = df.copy()
    if continent_col not in plot_df.columns:
        # Simple heuristic mapping for top locations
        def infer_continent(row):
            lat = row.get("latitude", 0)
            lon = row.get("longitude", 0)
            if lat > 35 and -15 < lon < 45:
                return "Europe"
            elif lat > 15 and -130 < lon < -60:
                return "North America"
            elif lat < 15 and -90 < lon < -30:
                return "South America"
            elif -40 < lat < 38 and -20 < lon < 55:
                return "Africa"
            elif lat > 0 and 55 < lon < 150:
                return "Asia"
            elif lat < 0 and 110 < lon < 180:
                return "Oceania"
            return "Other"

        plot_df[continent_col] = plot_df.apply(infer_continent, axis=1)

    cont_summary = plot_df.groupby(continent_col)[temp_col].mean().reset_index()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    bars = ax.bar(cont_summary[continent_col], cont_summary[temp_col], color="#2B6CB0", edgecolor="#1A365D")
    ax.set_title("Average Temperature by Continental Zone", fontweight="bold")
    ax.set_ylabel("Mean Temperature (°C)")
    ax.set_xlabel("Continent / Region")

    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"{h:.1f}°C", xy=(bar.get_x() + bar.get_width()/2, h),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9)

    fig.text(
        0.5, -0.06,
        "Interpretation: Africa and South America exhibit highest mean regional temperatures, reflecting tropical "
        "and sub-equatorial landmass distributions.",
        ha="center", fontsize=8, color="#4A5568", wrap=True
    )

    out_file = OUTPUTS_GRAPHS_DIR / "14_continent_comparisons.png"
    fig.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return str(out_file)

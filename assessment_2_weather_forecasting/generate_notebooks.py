"""Generator script creating all 7 standard Jupyter notebooks for Assessment 2."""

import nbformat as nbf
from pathlib import Path

NOTEBOOKS_DIR = Path(__file__).resolve().parent / "notebooks"
NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

def create_nb(filename, title, cells_content):
    nb = nbf.v4.new_notebook()
    nb["cells"] = []
    
    # Title header cell
    header = (
        f"# {title}\n\n"
        f"**Project:** Weather Intelligence Platform — Assessment 2: Weather Trend Forecasting  \n"
        f"**Developer:** Aanchal Singh  \n"
        f"**Organization:** PM Accelerator (Product Manager Accelerator)  \n"
        f"**Program Link:** [PM Accelerator](https://www.pmaccelerator.io/)\n"
    )
    nb["cells"].append(nbf.v4.new_markdown_cell(header))
    
    for ctype, content in cells_content:
        if ctype == "md":
            nb["cells"].append(nbf.v4.new_markdown_cell(content))
        elif ctype == "code":
            nb["cells"].append(nbf.v4.new_code_cell(content))
            
    out_path = NOTEBOOKS_DIR / filename
    with open(out_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Created notebook: {out_path.name}")


# 1. 01_data_understanding.ipynb
nb1_cells = [
    ("md", "## 1. Objective and Dataset Overview\nIn this notebook, we load the dataset, inspect columns and data types, examine memory usage, and validate the time-series structure of the `last_updated` column to verify whether it supports multi-step forecasting."),
    ("code", "import sys\nfrom pathlib import Path\nimport pandas as pd\n\n# Configure paths\nSRC_DIR = Path('..').resolve() / 'src'\nif str(SRC_DIR) not in sys.path:\n    sys.path.insert(0, str(SRC_DIR))\n\nfrom data_loader import load_dataset, inspect_dataset, validate_time_series_structure"),
    ("md", "## 2. Load Dataset\nWe load the raw Kaggle CSV if present in `data/raw/`, or load the verified multi-continent historical observations."),
    ("code", "df, provenance = load_dataset()\nprint('Data Source:', provenance['source'])\nprint('Dataset Shape:', df.shape)\ndf.head()"),
    ("md", "## 3. Comprehensive Dataset Inspection\nInspect total rows, columns, memory footprint, missing values, and column classifications."),
    ("code", "inspection = inspect_dataset(df)\nfor k, v in inspection.items():\n    if not isinstance(v, list):\n        print(f'{k}: {v}')"),
    ("md", "## 4. Time-Series Depth Validation\nCheck number of unique dates and sampling frequency per city to assess temporal forecasting suitability."),
    ("code", "validation = validate_time_series_structure(df)\nfor k, v in validation.items():\n    print(f'{k}: {v}')"),
]
create_nb("01_data_understanding.ipynb", "01. Dataset Understanding & Temporal Validation", nb1_cells)

# 2. 02_data_cleaning.ipynb
nb2_cells = [
    ("md", "## 1. Preprocessing Pipeline Overview\nWe clean column headers, remove duplicates, handle missing values (median for numerical, mode for categorical), parse dates, and construct lag/rolling features."),
    ("code", "import sys\nfrom pathlib import Path\nimport pandas as pd\n\nSRC_DIR = Path('..').resolve() / 'src'\nif str(SRC_DIR) not in sys.path:\n    sys.path.insert(0, str(SRC_DIR))\n\nfrom data_loader import load_dataset\nfrom preprocessing import preprocess_pipeline"),
    ("md", "## 2. Execute Preprocessing\nRuns end-to-end cleaning and saves clean data to `data/processed/weather_cleaned.csv`."),
    ("code", "df_raw, _ = load_dataset()\ndf_clean, metadata = preprocess_pipeline(df_raw)\nprint('Preprocessing Metadata:', metadata)\ndf_clean.info()"),
    ("md", "## 3. Verify Engineered Temporal and Lag Features\nInspect generated lag and rolling variables created without future data leakage."),
    ("code", "engineered_cols = [c for c in df_clean.columns if 'lag' in c or 'rolling' in c or 'sin' in c]\nprint('Engineered Features:', engineered_cols)\ndf_clean[['last_updated', 'temperature_celsius'] + engineered_cols[:4]].head()"),
]
create_nb("02_data_cleaning.ipynb", "02. Data Cleaning & Feature Engineering", nb2_cells)

# 3. 03_exploratory_analysis.ipynb
nb3_cells = [
    ("md", "## 1. Exploratory Data Analysis (EDA)\nGenerates statistical distributions, temperature boxplots by location, chronological trend lines, precipitation comparisons, and inter-feature correlation heatmaps."),
    ("code", "import sys\nfrom pathlib import Path\nimport pandas as pd\nimport matplotlib.pyplot as plt\n\nSRC_DIR = Path('..').resolve() / 'src'\nif str(SRC_DIR) not in sys.path:\n    sys.path.insert(0, str(SRC_DIR))\n\nfrom eda import run_full_eda, compute_basic_statistics\n\ndf = pd.read_csv('../data/processed/weather_cleaned.csv')\nstats = compute_basic_statistics(df)\nstats"),
    ("md", "## 2. Execute EDA Visualizations\nOutputs publication-grade figures saved to `outputs/graphs/`."),
    ("code", "eda_results = run_full_eda(df)\nprint('Generated figures:')\nfor g in eda_results['generated_graphs']:\n    print('-', g)"),
]
create_nb("03_exploratory_analysis.ipynb", "03. Exploratory Data Analysis (EDA)", nb3_cells)

# 4. 04_anomaly_detection.ipynb
nb4_cells = [
    ("md", "## 1. Anomaly Detection Methodologies\nCompares three distinct outlier detection frameworks:\n1. Tukey's Interquartile Range (IQR)\n2. Z-Score (standard deviations from mean)\n3. Isolation Forest (multivariate unsupervised tree partitioning)"),
    ("code", "import sys\nfrom pathlib import Path\nimport pandas as pd\n\nSRC_DIR = Path('..').resolve() / 'src'\nif str(SRC_DIR) not in sys.path:\n    sys.path.insert(0, str(SRC_DIR))\n\nfrom anomaly_detection import run_anomaly_detection_benchmark, plot_anomaly_detection_comparison\n\ndf = pd.read_csv('../data/processed/weather_cleaned.csv')\ndf_flagged, summary = run_anomaly_detection_benchmark(df)\nsummary"),
    ("md", "## 2. Plot Anomaly Comparison\nVisualizes the flagged anomaly points across methods."),
    ("code", "fig_path = plot_anomaly_detection_comparison(df_flagged)\nprint('Saved anomaly comparison chart to:', fig_path)"),
]
create_nb("04_anomaly_detection.ipynb", "04. Anomaly Detection & Extreme Event Analysis", nb4_cells)

# 5. 05_forecasting_models.ipynb
nb5_cells = [
    ("md", "## 1. Multi-Model Time-Series Forecasting\nTrains and evaluates models chronologically (80% train, 20% test):\n- Naive Baseline ($y_{t-1}$)\n- Moving Average (7-day window)\n- Exponential Smoothing\n- Ridge Autoregression\n- Random Forest Regressor\n- Gradient Boosting Regressor\n- Weighted Ensemble"),
    ("code", "import sys\nfrom pathlib import Path\nimport pandas as pd\n\nSRC_DIR = Path('..').resolve() / 'src'\nif str(SRC_DIR) not in sys.path:\n    sys.path.insert(0, str(SRC_DIR))\n\nfrom forecasting import train_and_evaluate_all_models\nfrom evaluation import evaluate_forecast_predictions\n\ndf = pd.read_csv('../data/processed/weather_cleaned.csv')\nresults = train_and_evaluate_all_models(df)\nmetrics_df = evaluate_forecast_predictions(results['y_test'], results['predictions'])\nmetrics_df"),
]
create_nb("05_forecasting_models.ipynb", "05. Multi-Model Forecasting & Ensemble Benchmarking", nb5_cells)

# 6. 06_advanced_analysis.ipynb
nb6_cells = [
    ("md", "## 1. Advanced Climatological, Environmental & Spatial Analysis\nExamines annual temperature climatology, seasonal distributions, particulate pollutant interactions, and global coordinate scatter maps."),
    ("code", "import sys\nfrom pathlib import Path\nimport pandas as pd\n\nSRC_DIR = Path('..').resolve() / 'src'\nif str(SRC_DIR) not in sys.path:\n    sys.path.insert(0, str(SRC_DIR))\n\nfrom climate_analysis import plot_monthly_climatology, plot_seasonal_distribution\nfrom air_quality import plot_air_quality_weather_interactions\nfrom spatial_analysis import plot_geographical_scatter, plot_continent_comparison\n\ndf = pd.read_csv('../data/processed/weather_cleaned.csv')\nprint('Plotting monthly climatology:', plot_monthly_climatology(df))\nprint('Plotting seasonal violin:', plot_seasonal_distribution(df))\nprint('Plotting air quality correlation:', plot_air_quality_weather_interactions(df))\nprint('Plotting spatial map:', plot_geographical_scatter(df))\nprint('Plotting continent bar:', plot_continent_comparison(df))"),
]
create_nb("06_advanced_analysis.ipynb", "06. Advanced Climate, Air Quality & Spatial Analysis", nb6_cells)

# 7. 07_model_evaluation.ipynb
nb7_cells = [
    ("md", "## 1. Model Evaluation, Residual Analysis & Diagnostic Verification\nEvaluates error distributions, residual normality, and feature importances."),
    ("code", "import sys\nfrom pathlib import Path\nimport pandas as pd\n\nSRC_DIR = Path('..').resolve() / 'src'\nif str(SRC_DIR) not in sys.path:\n    sys.path.insert(0, str(SRC_DIR))\n\nfrom forecasting import train_and_evaluate_all_models, split_chronological_data, prepare_feature_matrices\nfrom evaluation import evaluate_forecast_predictions, plot_actual_vs_predicted, plot_model_comparison_bar, plot_residuals\nfrom feature_importance import plot_feature_importances\n\ndf = pd.read_csv('../data/processed/weather_cleaned.csv')\nresults = train_and_evaluate_all_models(df)\nmetrics_df = evaluate_forecast_predictions(results['y_test'], results['predictions'])\nprint(metrics_df)\n\nplot_actual_vs_predicted(results['y_test'], results['predictions'], test_dates=results['test_dates'])\nplot_model_comparison_bar(metrics_df)\nplot_residuals(results['y_test'], results['predictions'])\n\ntrain_df, test_df = split_chronological_data(df)\nX_train, y_train, X_test, y_test, features = prepare_feature_matrices(train_df, test_df)\nplot_feature_importances(results['fitted_models']['random_forest'], features, X_test, y_test)"),
]
create_nb("07_model_evaluation.ipynb", "07. Model Evaluation & Feature Importance", nb7_cells)

print("All 7 notebooks successfully generated.")

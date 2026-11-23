# 🎓 PM Accelerator: Comprehensive Technical Interview Preparation Guide

**Project:** Weather Intelligence Platform (Dual Technical Assessments)  
**Developer:** Aanchal Singh  
**Organization:** PM Accelerator (Product Manager Accelerator)  
**Target Role:** Software Engineer / Data Scientist / Technical Product Manager  

---

## 🧭 How to Use This Guide
This guide is designed for a candidate preparing to explain both assessments with total confidence during a live technical interview. Every concept is broken down in plain English, with:
1. **What it does**
2. **Why it is needed**
3. **How it works**
4. **Input & Output**
5. **Technology used**
6. **"How I explain it to an interviewer"** (spoken-word script)
7. **25+ Anticipated Interviewer Questions with direct, authentic answers**

---

# PART I: ASSESSMENT 1 (BACKEND ENGINEERING)

### 1. What is FastAPI and why was it chosen?
- **What it is:** A modern, high-performance web framework for building REST APIs with Python 3.8+ using standard Python type hints.
- **Why it is needed:** It provides native asynchronous request processing (`async/await`), automatic OpenAPI (Swagger) interactive documentation, and fast serialization.
- **How it works:** When an HTTP request arrives, FastAPI matches the route path, validates incoming JSON using Pydantic models, injects database sessions via dependencies, and returns structured JSON responses.
- **Libraries used:** `fastapi`, `uvicorn`, `pydantic`.
- **How to explain in an interview:**  
  > *"I selected FastAPI because it combines the simplicity of Flask with the high concurrency and automatic schema validation of Pydantic. It automatically generates interactive Swagger docs at `/docs`, which makes debugging and team handoffs seamless."*

### 2. Why PostgreSQL instead of SQLite or in-memory databases?
- **What it is:** An enterprise-grade, open-source object-relational database management system (ORDBMS).
- **Why it is needed:** SQLite is a serverless file-based database that locks the entire file during write operations and does not enforce foreign keys by default. PostgreSQL provides full ACID compliance, multi-user concurrency (MVCC), rich data types, connection pooling, and strict relational constraints.
- **How it works:** PostgreSQL runs as a dedicated server listening on port 5432. FastAPI connects to it via the modern `psycopg` (version 3) binary driver.
- **How to explain in an interview:**  
  > *"For production backend systems, SQLite cannot handle concurrent write traffic without database lock contention. PostgreSQL provides true ACID transactions, multi-client connection pooling, and strict referential integrity with cascading deletes."*

### 3. What is SQLAlchemy and how does ORM work?
- **What it is:** The leading Python Object Relational Mapper (ORM) and SQL toolkit.
- **Why it is needed:** Writing raw SQL strings (`"SELECT * FROM ..."` ) is error-prone, vulnerable to SQL injection, and lacks object-oriented type safety.
- **How it works:** SQLAlchemy maps Python classes (`WeatherRecord`) to PostgreSQL tables (`weather_records`). Querying is done via Python methods: `db.query(WeatherRecord).filter(...)`.
- **How to explain in an interview:**  
  > *"SQLAlchemy translates my Python objects into safe, parameterized SQL queries behind the scenes. It handles connection pooling, prevents SQL injection, and manages transaction lifecycles cleanly."*

### 4. What does CRUD mean in our application?
- **C - CREATE (`POST /api/weather/search`):** Takes a location query and date bounds, resolves coordinates via geocoding, fetches daily weather from Open-Meteo, and inserts a parent `WeatherRecord` and child `DailyWeatherRecord` rows into PostgreSQL.
- **R - READ (`GET /api/weather/records`, `GET /api/weather/records/{id}`):** Retrieves saved records with pagination (`page`, `per_page`), search filtering (`q`), and date range bounds.
- **U - UPDATE (`PUT /api/weather/records/{id}`):** Edits the location or dates of an existing record, re-queries Open-Meteo for fresh data, and updates the database record and daily rows in an atomic transaction.
- **D - DELETE (`DELETE /api/weather/records/{id}`):** Permanently removes a record. Because the foreign key has `ON DELETE CASCADE`, all associated daily weather rows are automatically removed by PostgreSQL.

### 5. How does geocoding work?
- **What it does:** Converts any user input—such as a city name ("Tokyo"), postal code ("10001"), landmark ("Eiffel Tower"), or GPS pair ("40.71, -74.00")—into latitude, longitude, and country name.
- **How it works:** 
  1. Regular expression checks if the user already provided decimal coordinates (`lat, lon`).
  2. If text, queries Open-Meteo Geocoding API (`https://geocoding-api.open-meteo.com/v1/search`).
  3. If no match is found (e.g. detailed landmarks or zip codes), it seamlessly falls back to OpenStreetMap Nominatim.
- **How to explain in an interview:**  
  > *"To deliver a resilient user experience, I built a multi-tier geocoding resolver. It first tests for raw GPS coordinates via regex, then queries Open-Meteo's fast geocoding engine, and falls back to OpenStreetMap Nominatim for landmarks and postal codes."*

### 6. How does external weather API integration work?
- **APIs used:** Open-Meteo Forecast API and Open-Meteo Historical Archive API.
- **Why Open-Meteo:** Open-Meteo provides free, high-precision global atmospheric observations and forecasts up to 16 days without requiring paid commercial API keys.
- **Handling dates:** For dates older than 2 days, our backend queries the Archive API. For recent and future dates, it queries the Forecast API. If a user queries a date range spanning both (e.g. last week to next week), our backend queries both endpoints and merges the daily arrays chronologically.

### 7. How are data exports generated?
- **CSV:** Formatted into tabular rows where each daily weather observation forms an explicit row containing record ID, location, coordinates, dates, temperatures, rain, and wind.
- **JSON:** Formatted as structured JSON containing PM Accelerator metadata, developer credit (`Aanchal Singh`), and records with nested daily objects.
- **PDF:** Generated on the fly using `reportlab`. Formatted with executive headers, PM Accelerator branding, summary tables, and daily breakdown tables.

---

# PART II: ASSESSMENT 2 (DATA SCIENCE & MACHINE LEARNING)

### 1. What is Exploratory Data Analysis (EDA)?
- **What it is:** The foundational process of inspecting data through descriptive statistics and visualizations to discover underlying patterns, detect anomalies, test hypotheses, and verify assumptions before modeling.
- **Why it is needed:** Machine learning models mirror the biases and flaws in their training data. Without EDA, you cannot know if distributions are skewed, if features are correlated, or if data is missing.

### 2. Why is preprocessing necessary?
- Real-world data contains missing entries, inconsistent datetime strings, duplicate records, and disparate feature scales. Preprocessing standardizes features, handles missing values systematically (median for numerical, mode for categorical), and extracts cyclical date signals (`sin_month`, `cos_month`).

### 3. What is data leakage and how did we prevent it?
- **What it is:** Data leakage occurs when information from the future or test set is inadvertently leaked into the training set, causing unrealistically high test accuracy that collapses in production.
- **How we prevented it:** 
  1. We used **strict chronological splitting** (first 80% of dates for training, final 20% for testing). We never shuffled time-series records randomly.
  2. For lag features (`temp_lag_1`, `rolling_mean_3`), we used backward-looking shifts (`shift(1)`) so that current-day or future values are never part of historical predictors.

### 4. What are outliers vs. extreme weather events?
- **Outlier:** A statistical point that lies far from the center of the distribution (e.g., > 3 standard deviations or > $1.5 \times \text{IQR}$).
- **Key distinction:** In meteorology, an extreme value (like a 45°C heatwave or a -20°C polar vortex) is a **genuine physical reality**, not an erroneous sensor malfunction. We flag them using IQR, Z-Score, and Isolation Forest for analysis, but we do not blindly delete them.

### 5. Why does `last_updated` matter?
- `last_updated` provides the timestamp required to reconstruct a chronological time series. If a dataset only contains a single snapshot in time or lacks historical depth per city, traditional multi-step time-series forecasting (like ARIMA or lag-based regression) cannot be trained meaningfully. We audited this attribute openly and supplemented it with genuine multi-continent historical data from Open-Meteo.

### 6. What models did we implement and why?
1. **Naive Baseline ($y_{t-1}$):** Predicts today's temperature equals yesterday's temperature. Crucial baseline because weather has strong autoregressive inertia.
2. **Moving Average (7-Day):** Rolling 7-day mean. Smooths out daily noise.
3. **Exponential Smoothing:** Simple adaptive exponential smoothing with smoothing factor $\alpha = 0.35$.
4. **Ridge Autoregression:** Linear regression on lagged features with L2 regularization to prevent collinearity.
5. **Random Forest Regressor:** Non-linear ensemble of decision trees capturing interactions between latitude, season, and lagged temperatures.
6. **Gradient Boosting Regressor (HistGradientBoosting):** Sequentially builds trees to minimize residual errors.
7. **Weighted Ensemble:** Combines Gradient Boosting, Random Forest, and Exponential Smoothing.

### 7. What do the evaluation metrics mean?
- **MAE (Mean Absolute Error):** $\frac{1}{n}\sum |y_i - \hat{y}_i|$. The average error in actual degrees Celsius (°C). Direct and easily explained to business stakeholders.
- **MSE (Mean Squared Error):** $\frac{1}{n}\sum (y_i - \hat{y}_i)^2$. Penalizes large individual blunders more heavily due to squaring.
- **RMSE (Root Mean Squared Error):** $\sqrt{\text{MSE}}$. Square root of MSE, returning the error magnitude back into original °C units.
- **$R^2$ Score (Coefficient of Determination):** The proportion of variance explained by the model compared to predicting the horizontal mean line. $1.0$ is perfect; $0.0$ means no better than the mean; negative means worse than predicting the mean.
- **MAPE (Mean Absolute Percentage Error):** Average percentage discrepancy relative to the true value.

---

# PART III: 25 ANTICIPATED INTERVIEW QUESTIONS & ANSWERS

### Q1. Why did you choose this technology stack?
**Answer:** *"For Assessment 1, I chose FastAPI, PostgreSQL, and SQLAlchemy because they represent the industry standard for robust, type-safe backend architectures. FastAPI delivers native asynchronous throughput and Pydantic validation, while PostgreSQL guarantees ACID transactions and cascading foreign keys. For Assessment 2, Python's data ecosystem—pandas, scikit-learn, and matplotlib—provides the gold standard for statistical modeling and interpretable machine learning."*

### Q2. What was the most difficult engineering challenge you faced?
**Answer:** *"Handling cross-boundary date range queries in the weather service. Historical dates older than two days live in the Open-Meteo Archive API, while recent and future days live in the Forecast API. I designed a query router that detects whether a search spans both past and future, queries both endpoints concurrently, and merges the daily arrays into a seamless chronological series before saving to PostgreSQL."*

### Q3. How did you validate data in the backend?
**Answer:** *"I implemented multi-tier validation using Pydantic schemas. In `WeatherSearchRequest`, custom model validators ensure that `start_date <= end_date`, that dates cannot be earlier than the Open-Meteo historical boundary (1940-01-01), and that future dates do not exceed the 16-day forecast limit. Location queries are geocoded and verified before any weather request is executed."*

### Q4. How did you handle missing values in the data science pipeline?
**Answer:** *"I applied domain-appropriate imputation. For numerical features (temperature, precipitation, wind), I used median imputation because weather distributions often exhibit skewness, making the mean sensitive to extreme events. For categorical features (country, season), I used mode imputation."*

### Q5. How did you prevent data leakage during time-series forecasting?
**Answer:** *"I strictly enforced two rules: first, chronological train/test splitting (first 80% of dates for training, final 20% for testing) without random shuffling. Second, when engineering lag and rolling features, I used strictly backward-looking shifts (`shift(1)`) so no information from the target day or future horizon ever entered the feature matrix."*

### Q6. How did you choose the best forecasting model?
**Answer:** *"I evaluated models strictly on the holdout test partition, never on the training set. Ridge Autoregression (MAE 1.464°C, R² 0.9318) and Gradient Boosting (MAE 1.516°C, R² 0.9298) achieved the lowest test RMSE and highest variance explained. Selection was based on test-set RMSE and residual normality."*

### Q7. How do you know your model is actually forecasting and not just memorizing?
**Answer:** *"Because the model was evaluated exclusively on future unseen dates in the test partition. In addition, its performance beat the Naive Baseline ($y_{t-1}$), proving that the learned lag weights and temporal coordinates contribute genuine predictive signal rather than mere persistence memorization."*

### Q8. What were the limitations of the original Kaggle dataset?
**Answer:** *"When auditing the `last_updated` column, I found that the original Kaggle Global Weather Repository functions primarily as a cross-sectional snapshot across global cities rather than a continuous multi-month historical time series for each city. Rather than fabricating dates or manufacturing fake rows, I documented this limitation transparently and supplemented it with real historical observations from the Open-Meteo Archive API across global reference cities."*

### Q9. How does your relational database handle record updates and deletions?
**Answer:** *"The schema uses two tables: `weather_records` (parent) and `daily_weather_records` (child). The child table defines a foreign key referencing `weather_records.id` with `ON DELETE CASCADE`. When a user deletes a search record, PostgreSQL automatically deletes all child rows. On update, changes to dates or location trigger a fresh API fetch and re-populate the child rows inside an atomic transaction."*

### Q10. What happens if an external API (like Open-Meteo or YouTube) fails?
**Answer:** *"I built defensive fallbacks and timeout protection. Network calls use a 15-second timeout. For geocoding, if Open-Meteo fails, it falls back to Nominatim OSM. For YouTube, if the API key is missing or quota is exhausted, the backend returns a genuine YouTube search URL so the user is never blocked. Unhandled exceptions are caught by centralized FastAPI exception handlers returning clean JSON errors without exposing internal stack traces."*

### Q11. Did your ensemble model outperform the individual models?
**Answer:** *"In our evaluation, the Weighted Ensemble achieved an MAE of 2.066°C and R² of 0.8949, which was slightly lower than pure Ridge Autoregression (1.464°C) and Gradient Boosting (1.516°C). This occurred because Simple Exponential Smoothing had higher errors across multi-city pooled data. Rather than manipulating weights or claiming a false improvement, I reported this result honestly, explaining that ensembles only improve performance when component models exhibit uncorrelated error distributions."*

### Q12. What does $R^2$ mean in plain English?
**Answer:** *"R-squared represents the proportion of variation in temperature that our model successfully explains. An R² of 0.93 means our model accounts for 93% of the temperature fluctuations, leaving only 7% as unexplained variance or noise."*

### Q13. What is the difference between correlation and feature importance?
**Answer:** *"Correlation measures linear association between two individual variables ($r \in [-1, 1]$). Feature importance measures how much a machine learning model relies on a feature to make accurate predictions in the presence of other features. Neither implies physical causation."*

### Q14. What is Isolation Forest and how does it work?
**Answer:** *"Isolation Forest is an unsupervised tree-based algorithm that detects anomalies by randomly partitioning feature space. Because outliers are infrequent and structurally distinct, they require far fewer recursive splits to become isolated compared to normal points."*

### Q15. How do you distinguish between weather and climate?
**Answer:** *"Weather describes atmospheric conditions over short timeframes (hours, days, weeks). Climate is the statistical distribution of weather over multi-decadal timeframes (conventionally 30+ years). We cannot claim climate change trends from a 1-year weather dataset."*

### Q16. Why did you use Pydantic v2?
**Answer:** *"Pydantic v2 has its core validation engine rewritten in Rust, providing up to 5x faster data parsing and strict schema enforcement. It ensures that invalid types (e.g. non-date strings or out-of-range latitudes) are caught at the API boundary before hitting business logic."*

### Q17. How does connection pooling work in SQLAlchemy?
**Answer:** *"Opening a new TCP socket connection to PostgreSQL takes time. SQLAlchemy maintains a pool of pre-established connections (`pool_size=10`, `max_overflow=20`). When a request arrives, it checks out an active connection, uses it, and returns it to the pool in a finally block."*

### Q18. How did you structure the frontend?
**Answer:** *"I chose vanilla JavaScript, HTML5, and CSS3 without heavy frontend frameworks to keep the architecture transparent and fast. It uses Leaflet.js for interactive mapping and communicates with the FastAPI backend via asynchronous `fetch()` calls."*

### Q19. How did you test the backend?
**Answer:** *"I wrote 25 automated tests using Pytest and FastAPI's `TestClient`. I used a mock database fixture with SQLite in-memory and StaticPool to test all CRUD flows, validation rules, export generators, and error handling with 100% test isolation."*

### Q20. How did you test the data science module?
**Answer:** *"I wrote 14 automated tests in Assessment 2 testing dataset loading, missing value imputation, date component parsing, lag feature generation, chronological splitting, naive models, and MAPE calculation."*

### Q21. How are PDF exports generated?
**Answer:** *"We use `reportlab` to construct flowable documents. The PDF includes dynamic PM Accelerator headers, candidate attribution, executive summary paragraphs, and structured summary and daily observation tables."*

### Q22. How does the weather recommendation engine work?
**Answer:** *"It uses explainable, deterministic heuristic rules based on temperature, precipitation, and wind speed. For example, if precipitation > 1.0 mm or rain codes appear, it recommends indoor activities and waterproof gear. If temperatures drop below 0°C, it recommends heavy insulated coats."*

### Q23. What are lag features and why are they effective in weather forecasting?
**Answer:** *"Lag features represent observations from previous time steps (e.g., $T_{t-1}, T_{t-7}$). Atmospheric temperature exhibits strong thermal inertia; the air mass over a city does not jump randomly by 30°C in one day. Prior temperature values provide the strongest autoregressive baseline."*

### Q24. How would you deploy this project to production?
**Answer:** *"I would containerize the backend and frontend using Docker, deploy the FastAPI container onto a container runner (like Google Cloud Run or AWS ECS), configure managed PostgreSQL (such as Amazon RDS or GCP Cloud SQL), and set up Redis for caching frequent weather searches."*

### Q25. If you had one more week, what would you improve?
**Answer:** *"I would add Redis caching with a 30-minute TTL for current weather queries to minimize redundant external API calls, integrate weather radar map layers via RainViewer or OpenWeatherMap tile overlays, and implement multi-step recursive forecasting with deep learning architectures like Temporal Fusion Transformers."*

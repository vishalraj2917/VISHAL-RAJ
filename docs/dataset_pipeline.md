# Dataset & Preprocessing Pipeline Documentation (Phase 4)

## 1. Overview
This document describes the dataset loading, data cleaning, feature engineering, and scikit-learn preprocessing pipeline for the AI Air Quality Prediction System.

---

## 2. Dataset Schema & Features

### Pollutant Features (Air Quality)
- `pm25`: Fine Particulate Matter ($PM_{2.5}$ in $\mu g/m^3$)
- `pm10`: Coarse Particulate Matter ($PM_{10}$ in $\mu g/m^3$)
- `co`: Carbon Monoxide ($CO$ in $mg/m^3$ or $ppm$)
- `no2`: Nitrogen Dioxide ($NO_2$ in $\mu g/m^3$)
- `so2`: Sulfur Dioxide ($SO_2$ in $\mu g/m^3$)
- `o3`: Ozone ($O_3$ in $\mu g/m^3$)
- `aqi`: Air Quality Index (Prediction Target)

### Weather Features
- `temperature`: Ambient temperature in Celsius ($-50^\circ\text{C}$ to $60^\circ\text{C}$)
- `humidity`: Relative humidity percentage ($0\%$ to $100\%$)
- `wind_speed`: Surface wind speed in $m/s$ ($0$ to $150$)
- `pressure`: Atmospheric pressure in $hPa$ ($800$ to $1100$)

### Time & Cyclical Features
- `timestamp`: Datetime ISO formatted observation time
- `hour`: Hour of day ($0 - 23$)
- `day`: Day of month ($1 - 31$)
- `month`: Month of year ($1 - 12$)
- `day_of_week`: Day of week index ($0 = \text{Monday}, 6 = \text{Sunday}$)
- `is_weekend`: Binary flag ($1$ for Saturday/Sunday, $0$ otherwise)
- `hour_sin` / `hour_cos`: Continuous cyclical sine/cosine representation of diurnal cycle
- `month_sin` / `month_cos`: Continuous cyclical sine/cosine representation of annual seasonality

### Interaction Features
- `pm_ratio`: $\frac{PM_{2.5}}{PM_{10} + 1e-5}$ clipped to $[0.0, 1.5]$ (indicates combustion vs dust origin)
- `temp_humidity_idx`: $\frac{\text{temperature} \times \text{humidity}}{100.0}$ (apparent heat / vapor interaction)

---

## 3. Data Cleaning Operations
1. **Header Normalization**: Case-insensitive and alias mapping (`pm2.5` $\to$ `pm25`, `relative_humidity` $\to$ `humidity`, `temp` $\to$ `temperature`).
2. **Timestamp Validation**: Coerces invalid formats to `NaT`, drops invalid timestamps, and enforces ascending chronological order.
3. **Deduplication**: Identifies and eliminates redundant timestamp + location entries.
4. **Physical Domain Boundary Enforcement**: Values outside realistic limits (e.g. negative readings, sensor disconnection code `-99.0`) are replaced with `NaN`.
5. **Time-Aware Imputation**: Time-series forward fill ($\le 3$ steps) and backward fill ($\le 3$ steps), followed by column median fallback to ensure zero data leakage across splits.

---

## 4. Target Variable Calculation
- Primary Target: `aqi` (Air Quality Index).
- When raw datasets lack an explicit AQI column, composite AQI is calculated via the standard breakpoint sub-index maximum function:
  $$\text{AQI} = \max(\text{SubIndex}(PM_{2.5}), \text{SubIndex}(PM_{10}))$$

---

## 5. Train / Validation / Test Splitting Strategy
- **Chronological Split** (Time-series strict):
  - **Training Set (70%)**: Earliest chronological partition ($T_0 \to T_{train\_end}$)
  - **Validation Set (15%)**: Intermediate chronological partition ($T_{train\_end} \to T_{val\_end}$)
  - **Testing Set (15%)**: Most recent chronological partition ($T_{val\_end} \to T_{end}$)
- **No Data Leakage Guarantee**: $T_{train\_max} < T_{val\_min} < T_{test\_min}$.
- Scikit-learn `RobustScaler` / `SimpleImputer` is fitted exclusively on the Training set and then applied (`transform`) to Validation and Test partitions.

---

## 6. Execution Commands
To execute the pipeline using Python 3.13 in the virtual environment:
```powershell
cd backend
.venv\Scripts\python.exe -m app.ml.run_pipeline
```
To run the automated test suite:
```powershell
cd backend
.venv\Scripts\pytest.exe tests/test_ml_pipeline.py -v
```

# Phase 5: Machine Learning Model Development & Training Documentation

## 1. Overview
Phase 5 implements a robust, reproducible Machine Learning training, model selection, evaluation, and inference pipeline to forecast the continuous **Air Quality Index (AQI)**.

---

## 2. Dataset & Features
- **Dataset Source**: Chronologically partitioned datasets created in Phase 4:
  - `data/processed/train.csv` (3,024 rows — 70%)
  - `data/processed/val.csv` (648 rows — 15%)
  - `data/processed/test.csv` (648 rows — 15%)
- **Target Column**: `aqi` (Continuous numerical target $\to$ Regression problem)
- **Input Features (21 total)**:
  - **Pollutants**: `pm25`, `pm10`, `co`, `no2`, `so2`, `o3`
  - **Weather**: `temperature`, `humidity`, `wind_speed`, `pressure`
  - **Time & Cyclical**: `hour`, `day`, `month`, `day_of_week`, `is_weekend`, `hour_sin`, `hour_cos`, `month_sin`, `month_cos`
  - **Interactions**: `pm_ratio`, `temp_humidity_idx`

---

## 3. Data Leakage Prevention Strategy
1. **Strict Temporal Partitioning**: $\max(\text{Train Timestamp}) < \min(\text{Val Timestamp}) < \min(\text{Test Timestamp})$.
2. **Independent Preprocessing**: Feature scalers (`RobustScaler`) and imputers (`SimpleImputer`) are fitted **exclusively on the training partition**.
3. **Model Selection Isolation**: Model hyperparameter comparison and selection are performed strictly on the **Validation set**. The **Test set** is evaluated only once after the best model is finalized.

---

## 4. Models Evaluated & Validation Results

| Model | Validation MAE | Validation MSE | Validation RMSE | Validation $R^2$ | Validation MAPE (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Dummy (Baseline)** | 12.7618 | 228.2552 | 15.1081 | -0.0355 | 51.00% |
| **Linear Regression** | 1.6183 | 5.9889 | 2.4472 | 0.9728 | 5.05% |
| **Ridge Regression** | 1.6105 | 5.9803 | 2.4455 | 0.9729 | 5.01% |
| **Random Forest** | 0.3635 | 2.2553 | 1.5018 | 0.9898 | 0.98% |
| **Gradient Boosting** | **0.4387** | **1.3857** | **1.1772** | **0.9937** | **1.34%** |
| **HistGradientBoosting** | 0.5135 | 1.6986 | 1.3033 | 0.9923 | 1.49% |

**Selected Champion Model**: **Gradient Boosting Regressor** (Achieved lowest Validation RMSE: **1.1772** and $R^2$: **0.9937**).

---

## 5. Final Test Set Evaluation
The champion **Gradient Boosting** model was evaluated on the unseen test set (`data/processed/test.csv`):
- **Test MAE**: `0.4768`
- **Test MSE**: `1.9040`
- **Test RMSE**: `1.3798`
- **Test $R^2$**: `0.9914`
- **Test MAPE**: `1.89%`

---

## 6. Generated Artifacts
- **Model Files**:
  - `models/best_model.joblib`: Serialized champion Gradient Boosting model
  - `models/preprocessor.joblib`: Serialized fitted ColumnTransformer pipeline
- **Metrics & Comparison**:
  - `models/model_comparison.csv`: Validation metrics table across all models
  - `models/final_metrics.json`: Final test evaluation metrics
  - `models/feature_importance.csv`: Sorted feature importance rankings
  - `models/model_metadata.json`: Full model provenance & configuration metadata
- **Figures**:
  - `reports/figures/actual_vs_predicted.png`
  - `reports/figures/residuals.png`
  - `reports/figures/model_comparison.png`
  - `reports/figures/feature_importance.png`

---

## 7. Execution Commands

### Training Pipeline CLI
```powershell
python -m ml.train
```

### Running Test Suite
```powershell
cd backend
.venv\Scripts\pytest.exe tests/ -v
```

### Python Prediction Utility
```python
from ml.predict import predict_aqi

sample = {
    "pm25": 45.2,
    "pm10": 85.0,
    "co": 0.8,
    "no2": 24.5,
    "so2": 11.2,
    "o3": 28.0,
    "temperature": 27.5,
    "humidity": 62.0,
    "wind_speed": 3.8,
    "pressure": 1012.5,
    "hour": 14,
    "day": 15,
    "month": 6,
    "day_of_week": 2,
    "is_weekend": 0,
}

predicted_aqi = predict_aqi(sample)
print(f"Predicted AQI: {predicted_aqi}")
```

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import joblib

from ml.evaluate import calculate_metrics
from ml.model_utils import resolve_project_path, load_datasets, FEATURE_COLUMNS
from ml.predict import AQIPredictor, predict_aqi
from ml.train import train_and_evaluate_models


@pytest.fixture
def synthetic_train_val_test():
    """Generates fast synthetic datasets for isolated unit testing."""
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        "pm25": np.random.uniform(10, 80, n),
        "pm10": np.random.uniform(20, 150, n),
        "co": np.random.uniform(0.1, 2.0, n),
        "no2": np.random.uniform(10, 40, n),
        "so2": np.random.uniform(5, 25, n),
        "o3": np.random.uniform(5, 35, n),
        "temperature": np.random.uniform(15, 35, n),
        "humidity": np.random.uniform(30, 90, n),
        "wind_speed": np.random.uniform(1, 10, n),
        "pressure": np.random.uniform(1005, 1020, n),
        "hour": np.random.randint(0, 24, n),
        "day": np.random.randint(1, 29, n),
        "month": np.random.randint(1, 13, n),
        "day_of_week": np.random.randint(0, 7, n),
        "is_weekend": np.random.choice([0, 1], n),
        "hour_sin": np.sin(2 * np.pi * np.random.randint(0, 24, n) / 24.0),
        "hour_cos": np.cos(2 * np.pi * np.random.randint(0, 24, n) / 24.0),
        "month_sin": np.sin(2 * np.pi * np.random.randint(1, 13, n) / 12.0),
        "month_cos": np.cos(2 * np.pi * np.random.randint(1, 13, n) / 12.0),
        "pm_ratio": np.random.uniform(0.4, 0.9, n),
        "temp_humidity_idx": np.random.uniform(5, 30, n),
    })
    # AQI continuous target
    df["aqi"] = df["pm25"] * 1.5 + np.random.normal(0, 1.0, n)
    df["timestamp"] = pd.date_range("2025-01-01", periods=n, freq="h")

    train_df = df.iloc[:70].copy()
    val_df = df.iloc[70:85].copy()
    test_df = df.iloc[85:].copy()
    return train_df, val_df, test_df


def test_calculate_metrics():
    y_true = np.array([50.0, 100.0, 150.0, 200.0])
    y_pred = np.array([52.0, 98.0, 149.0, 201.0])
    m = calculate_metrics(y_true, y_pred)

    assert "mae" in m
    assert "rmse" in m
    assert "r2" in m
    assert "mape" in m
    assert m["rmse"] < 3.0
    assert m["r2"] > 0.95


def test_load_datasets_and_target_detection():
    train_df, val_df, test_df, feature_cols, target_col = load_datasets()
    assert len(train_df) > 0
    assert len(val_df) > 0
    assert len(test_df) > 0
    assert target_col == "aqi"
    assert len(feature_cols) == 21


def test_prediction_utility_single_and_batch():
    sample = {
        "pm25": 30.0,
        "pm10": 60.0,
        "co": 0.5,
        "no2": 15.0,
        "so2": 8.0,
        "o3": 20.0,
        "temperature": 25.0,
        "humidity": 50.0,
        "wind_speed": 4.0,
        "pressure": 1013.0,
        "hour": 12,
        "day": 1,
        "month": 5,
        "day_of_week": 3,
        "is_weekend": 0,
    }
    pred = predict_aqi(sample)
    assert isinstance(pred, float)
    assert pred >= 0.0

    predictor = AQIPredictor()
    batch_preds = predictor.predict([sample, sample])
    assert len(batch_preds) == 2
    assert batch_preds[0] == batch_preds[1]


def test_model_training_and_artifact_saving(tmp_path, synthetic_train_val_test):
    train_df, val_df, test_df = synthetic_train_val_test

    train_file = tmp_path / "train.csv"
    val_file = tmp_path / "val.csv"
    test_file = tmp_path / "test.csv"
    train_df.to_csv(train_file, index=False)
    val_df.to_csv(val_file, index=False)
    test_df.to_csv(test_file, index=False)

    # Use existing fitted preprocessor
    result = train_and_evaluate_models(
        train_path=str(train_file),
        val_path=str(val_file),
        test_path=str(test_file),
        models_dir=str(tmp_path / "models"),
    )

    assert "best_model_name" in result
    assert result["best_model"] is not None
    assert (tmp_path / "models" / "best_model.joblib").exists()
    assert (tmp_path / "models" / "model_comparison.csv").exists()
    assert (tmp_path / "models" / "final_metrics.json").exists()
    assert (tmp_path / "models" / "model_metadata.json").exists()

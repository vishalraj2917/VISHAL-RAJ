import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os
import joblib

from app.ml.data_loader import DataLoader
from app.ml.preprocessing import DataCleaner
from app.ml.feature_engineering import FeatureEngineer, calculate_sub_aqi_pm25, derive_composite_aqi
from app.ml.dataset import AirQualityDatasetPipeline
from app.ml.generate_demo_data import generate_demo_dataset


@pytest.fixture
def sample_raw_dataframe():
    dates = pd.date_range("2025-01-01", periods=100, freq="h")
    df = pd.DataFrame({
        "timestamp": dates,
        "pm25": np.random.uniform(10, 100, 100),
        "pm10": np.random.uniform(20, 200, 100),
        "co": np.random.uniform(0.1, 2.0, 100),
        "no2": np.random.uniform(10, 50, 100),
        "so2": np.random.uniform(5, 30, 100),
        "o3": np.random.uniform(5, 40, 100),
        "aqi": np.random.uniform(20, 150, 100),
        "temperature": np.random.uniform(15, 35, 100),
        "humidity": np.random.uniform(30, 90, 100),
        "wind_speed": np.random.uniform(1, 10, 100),
        "pressure": np.random.uniform(1005, 1020, 100),
        "city": "Bengaluru",
    })
    return df


def test_data_loader_normalization():
    loader = DataLoader()
    raw = pd.DataFrame({
        "Date Time": ["2025-01-01 00:00:00"],
        "PM2.5": [35.5],
        "Relative Humidity": [60.0],
        "Temp": [25.0],
    })
    normalized = loader.normalize_columns(raw)
    assert "timestamp" in normalized.columns
    assert "pm25" in normalized.columns
    assert "humidity" in normalized.columns
    assert "temperature" in normalized.columns


def test_data_cleaner_anomalies_and_duplicates(sample_raw_dataframe):
    df = sample_raw_dataframe.copy()
    # Inject negative values and duplicates
    df.loc[0, "pm25"] = -50.0
    df.loc[1, "temperature"] = 150.0  # Impossible high temp
    df.loc[2, "humidity"] = np.nan
    df = pd.concat([df, df.iloc[0:2]], ignore_index=True)

    cleaner = DataCleaner()
    cleaned = cleaner.clean(df)

    assert len(cleaned) == 100  # Duplicates removed
    assert not cleaned["pm25"].isna().any()  # Imputed
    assert (cleaned["pm25"] >= 0).all()  # No negative values
    assert (cleaned["temperature"] <= 60.0).all()
    stats = cleaner.get_stats()
    assert stats["duplicates_removed"] == 2


def test_feature_engineering(sample_raw_dataframe):
    fe = FeatureEngineer()
    featured = fe.transform(sample_raw_dataframe)

    assert "hour" in featured.columns
    assert "day" in featured.columns
    assert "month" in featured.columns
    assert "day_of_week" in featured.columns
    assert "hour_sin" in featured.columns
    assert "pm_ratio" in featured.columns
    assert "temp_humidity_idx" in featured.columns
    assert (featured["pm_ratio"] >= 0).all()


def test_chronological_splitting_no_leakage(sample_raw_dataframe):
    pipeline = AirQualityDatasetPipeline(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15)
    train_df, val_df, test_df = pipeline.chronological_split(sample_raw_dataframe)

    assert len(train_df) == 70
    assert len(val_df) == 15
    assert len(test_df) == 15

    # Check temporal ordering
    assert train_df["timestamp"].max() < val_df["timestamp"].min()
    assert val_df["timestamp"].max() < test_df["timestamp"].min()


def test_full_pipeline_and_artifact_persistence(tmp_path):
    demo_csv = tmp_path / "demo.csv"
    generate_demo_dataset(str(demo_csv), n_days=10)

    pipeline = AirQualityDatasetPipeline()
    result = pipeline.process(str(demo_csv), is_file=True)

    assert "X_train" in result
    assert "y_train" in result
    assert not np.isnan(result["X_train"]).any()
    assert not np.isnan(result["X_val"]).any()
    assert not np.isnan(result["X_test"]).any()

    # Save artifacts
    artifacts = pipeline.save_artifacts(
        result,
        output_dir=tmp_path / "processed",
        preprocessor_path=tmp_path / "models" / "preprocessor.joblib",
    )

    assert Path(artifacts["train_file"]).exists()
    assert Path(artifacts["val_file"]).exists()
    assert Path(artifacts["test_file"]).exists()
    assert Path(artifacts["preprocessor_file"]).exists()

    # Load back the scaler and verify transformation
    loaded_preprocessor = joblib.load(artifacts["preprocessor_file"])
    transformed = loaded_preprocessor.transform(result["test_df"][result["features"]])
    assert transformed.shape == result["X_test"].shape

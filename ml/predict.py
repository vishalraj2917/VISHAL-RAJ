from pathlib import Path
from typing import Dict, Any, Union, List, Optional
import pandas as pd
import numpy as np
import joblib

from ml.model_utils import resolve_project_path, FEATURE_COLUMNS


class AQIPredictor:
    """
    Reusable production inference utility for predicting Air Quality Index (AQI).
    Loads the trained best model and preprocessing transformation pipeline.
    """

    def __init__(
        self,
        model_path: Union[str, Path] = "models/best_model.joblib",
        preprocessor_path: Union[str, Path] = "models/preprocessor.joblib",
    ):
        self.model_path = resolve_project_path(model_path)
        self.preprocessor_path = resolve_project_path(preprocessor_path)

        if not self.model_path.exists():
            raise FileNotFoundError(f"Trained model not found at: {self.model_path}")
        if not self.preprocessor_path.exists():
            raise FileNotFoundError(f"Preprocessor artifact not found at: {self.preprocessor_path}")

        self.model = joblib.load(self.model_path)
        self.preprocessor = joblib.load(self.preprocessor_path)

    def predict(self, input_data: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]) -> np.ndarray:
        """
        Validates input, applies preprocessor transformations, and computes AQI predictions.
        """
        if isinstance(input_data, dict):
            df = pd.DataFrame([input_data])
        elif isinstance(input_data, list):
            df = pd.DataFrame(input_data)
        elif isinstance(input_data, pd.DataFrame):
            df = input_data.copy()
        else:
            raise TypeError("input_data must be a DataFrame, dict, or list of dicts.")

        # Ensure all required features exist (fill missing with defaults if needed)
        missing_features = [f for f in FEATURE_COLUMNS if f not in df.columns]
        if missing_features:
            # Handle derived features dynamically if basic pollutants and timestamp/time exist
            if "hour" in df.columns and "hour_sin" not in df.columns:
                df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24.0)
                df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24.0)
            if "month" in df.columns and "month_sin" not in df.columns:
                df["month_sin"] = np.sin(2 * np.pi * (df["month"] - 1) / 12.0)
                df["month_cos"] = np.cos(2 * np.pi * (df["month"] - 1) / 12.0)
            if "pm25" in df.columns and "pm10" in df.columns and "pm_ratio" not in df.columns:
                df["pm_ratio"] = (df["pm25"] / (df["pm10"] + 1e-5)).clip(0.0, 1.5)
            if "temperature" in df.columns and "humidity" in df.columns and "temp_humidity_idx" not in df.columns:
                df["temp_humidity_idx"] = (df["temperature"] * df["humidity"]) / 100.0

        # Select only required feature columns
        available_features = [f for f in FEATURE_COLUMNS if f in df.columns]
        for f in FEATURE_COLUMNS:
            if f not in df.columns:
                df[f] = 0.0

        X_input = df[FEATURE_COLUMNS]

        # Transform using preprocessor
        X_scaled = self.preprocessor.transform(X_input)

        # Predict
        predictions = self.model.predict(X_scaled)
        # Ensure non-negative physical AQI predictions
        predictions = np.clip(predictions, 0.0, 1000.0)

        return predictions

    def predict_single(self, input_dict: Dict[str, Any]) -> float:
        """
        Convenience method to predict AQI for a single observation dictionary.
        """
        preds = self.predict(input_dict)
        return float(round(preds[0], 2))


def predict_aqi(input_data: Union[pd.DataFrame, Dict[str, Any]]) -> Union[float, np.ndarray]:
    """
    Standalone helper function for AQI prediction.
    """
    predictor = AQIPredictor()
    if isinstance(input_data, dict):
        return predictor.predict_single(input_data)
    return predictor.predict(input_data)

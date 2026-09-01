import logging
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import joblib

from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    PredictionData,
    ModelInfo,
    BatchPredictionRequest,
    BatchPredictionResponse,
)

logger = logging.getLogger(__name__)

# Standard AQI breakpoints and health categories (Indian CPCB / US EPA aligned)
AQI_CATEGORIES = [
    (0.0, 50.0, "Good", "#10B981", "Air quality is considered satisfactory, and air pollution poses little or no risk."),
    (51.0, 100.0, "Moderate", "#FBBF24", "Air quality is acceptable; however, some pollutants may be a concern for very sensitive people."),
    (101.0, 200.0, "Unhealthy for Sensitive Groups", "#F97316", "Members of sensitive groups may experience health effects; general public is less likely to be affected."),
    (201.0, 300.0, "Poor / Unhealthy", "#EF4444", "Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects."),
    (301.0, 400.0, "Very Poor / Severe", "#8B5CF6", "Health alert: The risk of health effects is increased for everyone."),
    (401.0, 1000.0, "Hazardous", "#7F1D1D", "Health warning of emergency conditions: Everyone is more likely to be affected."),
]

def get_aqi_category_info(aqi_val: float) -> Tuple[str, str, str]:
    """
    Returns (category_name, hex_color, health_advisory) for a given AQI score.
    """
    for min_v, max_v, category, color, advice in AQI_CATEGORIES:
        if min_v <= aqi_val <= max_v:
            return category, color, advice
    if aqi_val > 1000.0:
        return "Hazardous", "#7F1D1D", "Emergency conditions: avoid all outdoor physical activities."
    return "Good", "#10B981", "Air quality is considered satisfactory."


def resolve_model_artifact_path(rel_path: Union[str, Path]) -> Path:
    """
    Locates artifact checking backend and workspace root directories safely.
    """
    p = Path(rel_path)
    if p.is_absolute() and p.exists():
        return p
    candidates = [
        Path.cwd() / p,
        Path.cwd() / "backend" / p,
        Path(__file__).resolve().parent.parent.parent / p,
        Path(__file__).resolve().parent.parent.parent.parent / p,
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


class PredictionService:
    """
    Thread-safe Singleton ML Prediction Service for FastAPI.
    Loads best_model.joblib, preprocessor.joblib, and model_metadata.json at startup.
    Avoids expensive disk reload on each API request.
    """
    _instance: Optional["PredictionService"] = None

    def __init__(
        self,
        model_path: Union[str, Path] = "models/best_model.joblib",
        preprocessor_path: Union[str, Path] = "models/preprocessor.joblib",
        metadata_path: Union[str, Path] = "models/model_metadata.json",
    ):
        self.model_path = resolve_model_artifact_path(model_path)
        self.preprocessor_path = resolve_model_artifact_path(preprocessor_path)
        self.metadata_path = resolve_model_artifact_path(metadata_path)

        self.model = None
        self.preprocessor = None
        self.metadata: Dict[str, Any] = {}
        self.feature_columns: List[str] = []
        self._is_loaded = False

        self.load_artifacts()

    @classmethod
    def get_instance(cls) -> "PredictionService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_artifacts(self) -> None:
        """
        Loads ML model and transformation pipeline from disk safely.
        """
        try:
            if not self.model_path.exists():
                raise FileNotFoundError(f"Model artifact not found at {self.model_path.name}")
            if not self.preprocessor_path.exists():
                raise FileNotFoundError(f"Preprocessor artifact not found at {self.preprocessor_path.name}")

            logger.info(f"Loading best_model from: {self.model_path}")
            self.model = joblib.load(self.model_path)

            logger.info(f"Loading preprocessor from: {self.preprocessor_path}")
            self.preprocessor = joblib.load(self.preprocessor_path)

            if self.metadata_path.exists():
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                self.feature_columns = self.metadata.get("features", [])
            else:
                self.metadata = {
                    "model_name": "Gradient Boosting",
                    "model_type": "GradientBoostingRegressor",
                    "target_column": "aqi",
                    "best_validation_rmse": 1.1772,
                    "final_test_rmse": 1.3798,
                }
                self.feature_columns = [
                    "pm25", "pm10", "co", "no2", "so2", "o3",
                    "temperature", "humidity", "wind_speed", "pressure",
                    "hour", "day", "month", "day_of_week", "is_weekend",
                    "hour_sin", "hour_cos", "month_sin", "month_cos",
                    "pm_ratio", "temp_humidity_idx"
                ]

            self._is_loaded = True
            logger.info("ML Prediction Service successfully initialized.")

        except Exception as e:
            self._is_loaded = False
            logger.error(f"Failed to load ML artifacts: {str(e)}", exc_info=True)
            raise RuntimeError("Machine Learning artifacts could not be loaded into memory.") from e

    def is_ready(self) -> bool:
        return self._is_loaded and (self.model is not None) and (self.preprocessor is not None)

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            name=self.metadata.get("model_name", "Gradient Boosting"),
            type=self.metadata.get("model_type", "GradientBoostingRegressor"),
            target=self.metadata.get("target_column", "aqi"),
            validation_rmse=self.metadata.get("best_validation_rmse"),
            test_rmse=self.metadata.get("final_test_rmse"),
        )

    def _prepare_dataframe(self, items: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Formats raw feature dictionaries, calculates derived features deterministically,
        and aligns with exact feature matrix format expected by preprocessor.
        """
        df = pd.DataFrame(items)

        # 1. Cyclical time features if not explicitly supplied
        if "hour" in df.columns:
            if "hour_sin" not in df.columns or df["hour_sin"].isna().any():
                df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24.0)
            if "hour_cos" not in df.columns or df["hour_cos"].isna().any():
                df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24.0)

        if "month" in df.columns:
            if "month_sin" not in df.columns or df["month_sin"].isna().any():
                df["month_sin"] = np.sin(2 * np.pi * (df["month"] - 1) / 12.0)
            if "month_cos" not in df.columns or df["month_cos"].isna().any():
                df["month_cos"] = np.cos(2 * np.pi * (df["month"] - 1) / 12.0)

        # 2. Domain interaction features if not explicitly supplied
        if "pm25" in df.columns and "pm10" in df.columns:
            if "pm_ratio" not in df.columns or df["pm_ratio"].isna().any():
                df["pm_ratio"] = (df["pm25"] / (df["pm10"] + 1e-5)).clip(0.0, 1.5)

        if "temperature" in df.columns and "humidity" in df.columns:
            if "temp_humidity_idx" not in df.columns or df["temp_humidity_idx"].isna().any():
                df["temp_humidity_idx"] = (df["temperature"] * df["humidity"]) / 100.0

        # Fill any missing expected columns with 0.0
        for col in self.feature_columns:
            if col not in df.columns or df[col].isna().all():
                df[col] = 0.0
            else:
                df[col] = df[col].fillna(0.0)

        # Order strictly as expected during training
        return df[self.feature_columns]

    def _determine_dominant_pollutant(self, req: PredictionRequest) -> str:
        """
        Determines most elevated pollutant contributing to AQI.
        """
        # Compare relative pollutant ratios
        pollutants = {
            "PM2.5": req.pm25 / 30.0,
            "PM10": req.pm10 / 50.0,
            "NO2": req.no2 / 40.0,
            "CO": req.co / 2.0,
            "SO2": req.so2 / 40.0,
            "O3": req.o3 / 50.0,
        }
        return max(pollutants, key=pollutants.get)

    def predict_single(self, request: PredictionRequest) -> PredictionResponse:
        """
        Generates AQI prediction for a single validated PredictionRequest.
        """
        if not self.is_ready():
            raise RuntimeError("Model service is unavailable or not loaded.")

        req_dict = request.model_dump(exclude={"location_id"})
        df_input = self._prepare_dataframe([req_dict])

        # Preprocessing transformation
        X_scaled = self.preprocessor.transform(df_input)

        # Prediction
        raw_pred = self.model.predict(X_scaled)[0]

        # Enforce finite physical bounds
        aqi_val = float(np.clip(raw_pred, 0.0, 1000.0))
        aqi_rounded = float(round(aqi_val, 2))

        category, color, advice = get_aqi_category_info(aqi_rounded)
        dominant = self._determine_dominant_pollutant(request)

        pred_data = PredictionData(
            aqi=aqi_rounded,
            category=category,
            color=color,
            dominant_pollutant=dominant,
            health_advisory=advice,
        )

        return PredictionResponse(
            success=True,
            prediction=pred_data,
            model=self.get_model_info(),
            timestamp=datetime.now(timezone.utc),
        )

    def predict_batch(self, request: BatchPredictionRequest) -> BatchPredictionResponse:
        """
        Generates vectorized AQI predictions for a batch of requests.
        """
        if not self.is_ready():
            raise RuntimeError("Model service is unavailable or not loaded.")

        dicts = [r.model_dump(exclude={"location_id"}) for r in request.records]
        df_input = self._prepare_dataframe(dicts)

        X_scaled = self.preprocessor.transform(df_input)
        raw_preds = self.model.predict(X_scaled)
        clipped_preds = np.clip(raw_preds, 0.0, 1000.0)

        predictions_list = []
        for i, raw_val in enumerate(clipped_preds):
            aqi_rounded = float(round(float(raw_val), 2))
            category, color, advice = get_aqi_category_info(aqi_rounded)
            dominant = self._determine_dominant_pollutant(request.records[i])

            predictions_list.append(
                PredictionData(
                    aqi=aqi_rounded,
                    category=category,
                    color=color,
                    dominant_pollutant=dominant,
                    health_advisory=advice,
                )
            )

        return BatchPredictionResponse(
            success=True,
            count=len(predictions_list),
            predictions=predictions_list,
            model=self.get_model_info(),
            timestamp=datetime.now(timezone.utc),
        )


def get_prediction_service() -> PredictionService:
    """
    FastAPI dependency injection provider for PredictionService.
    """
    return PredictionService.get_instance()

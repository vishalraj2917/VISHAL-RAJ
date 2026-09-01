import logging
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional, Union
import numpy as np
import pandas as pd
import joblib
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.impute import SimpleImputer

from app.ml.data_loader import DataLoader
from app.ml.preprocessing import DataCleaner
from app.ml.feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)

# Standard model feature set
MODEL_FEATURES = [
    # Pollutants
    "pm25",
    "pm10",
    "co",
    "no2",
    "so2",
    "o3",
    # Weather
    "temperature",
    "humidity",
    "wind_speed",
    "pressure",
    # Time features
    "hour",
    "day",
    "month",
    "day_of_week",
    "is_weekend",
    "hour_sin",
    "hour_cos",
    "month_sin",
    "month_cos",
    # Interaction features
    "pm_ratio",
    "temp_humidity_idx",
]

TARGET_COLUMN = "aqi"


class AirQualityDatasetPipeline:
    """
    Complete Air Quality ML Dataset Pipeline:
    - Loads raw data (CSV or dicts)
    - Cleans anomalies and imputes missing values
    - Engineers time and pollution features
    - Splits chronologically (Train: 70%, Val: 15%, Test: 15%)
    - Fits sklearn preprocessing pipeline only on training data
    - Transforms validation and test sets without data leakage
    - Persists processed datasets and scaler artifacts
    """

    def __init__(
        self,
        features: Optional[List[str]] = None,
        target: str = TARGET_COLUMN,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
    ):
        self.feature_names = features or MODEL_FEATURES
        self.target_name = target
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio

        self.data_loader = DataLoader()
        self.data_cleaner = DataCleaner()
        self.feature_engineer = FeatureEngineer()
        self.preprocessor_pipeline: Optional[ColumnTransformer] = None

    def build_sklearn_pipeline(self, numeric_cols: List[str]) -> ColumnTransformer:
        """
        Creates a scikit-learn ColumnTransformer with median imputation and RobustScaler.
        """
        num_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", RobustScaler()),
            ]
        )
        preprocessor = ColumnTransformer(
            transformers=[
                ("num", num_transformer, numeric_cols),
            ],
            remainder="passthrough",
        )
        return preprocessor

    def chronological_split(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Splits data chronologically to strictly prevent lookahead bias / data leakage.
        """
        # Ensure ordering
        if "timestamp" in df.columns:
            df = df.sort_values(by="timestamp").reset_index(drop=True)

        n = len(df)
        train_end = int(n * self.train_ratio)
        val_end = int(n * (self.train_ratio + self.val_ratio))

        train_df = df.iloc[:train_end].copy().reset_index(drop=True)
        val_df = df.iloc[train_end:val_end].copy().reset_index(drop=True)
        test_df = df.iloc[val_end:].copy().reset_index(drop=True)

        logger.info(
            f"Chronological split: Train={len(train_df)} ({self.train_ratio*100}%), "
            f"Val={len(val_df)} ({self.val_ratio*100}%), Test={len(test_df)} ({self.test_ratio*100}%)"
        )
        return train_df, val_df, test_df

    def process(
        self, source_data: Any, is_file: bool = True
    ) -> Dict[str, Any]:
        """
        Runs the full end-to-end dataset pipeline.
        """
        # 1. Load Data
        if is_file:
            raw_df = self.data_loader.load_csv(source_data)
        else:
            raw_df = self.data_loader.load_from_records(source_data)

        # 2. Clean Data
        cleaned_df = self.data_cleaner.clean(raw_df)

        # 3. Feature Engineering
        featured_df = self.feature_engineer.transform(cleaned_df)

        # 4. Filter to available modeling features
        available_features = [f for f in self.feature_names if f in featured_df.columns]
        if not available_features:
            raise ValueError("No matching model features found in engineered dataset.")

        # Ensure target is present
        if self.target_name not in featured_df.columns:
            raise ValueError(f"Target column '{self.target_name}' not found.")

        # 5. Chronological Split
        train_df, val_df, test_df = self.chronological_split(featured_df)

        X_train_df = train_df[available_features]
        y_train = train_df[self.target_name].values

        X_val_df = val_df[available_features]
        y_val = val_df[self.target_name].values

        X_test_df = test_df[available_features]
        y_test = test_df[self.target_name].values

        # 6. Fit Preprocessor ONLY on Training set (Avoid Leakage)
        self.preprocessor_pipeline = self.build_sklearn_pipeline(available_features)
        X_train_scaled = self.preprocessor_pipeline.fit_transform(X_train_df)
        X_val_scaled = self.preprocessor_pipeline.transform(X_val_df)
        X_test_scaled = self.preprocessor_pipeline.transform(X_test_df)

        cleaning_stats = self.data_cleaner.get_stats()

        return {
            "features": available_features,
            "target": self.target_name,
            "raw_df": raw_df,
            "cleaned_df": cleaned_df,
            "featured_df": featured_df,
            "train_df": train_df,
            "val_df": val_df,
            "test_df": test_df,
            "X_train": X_train_scaled,
            "y_train": y_train,
            "X_val": X_val_scaled,
            "y_val": y_val,
            "X_test": X_test_scaled,
            "y_test": y_test,
            "cleaning_stats": cleaning_stats,
            "preprocessor": self.preprocessor_pipeline,
        }

    def save_artifacts(
        self,
        pipeline_output: Dict[str, Any],
        output_dir: Union[str, Path] = "data/processed",
        preprocessor_path: Union[str, Path] = "models/preprocessor.joblib",
    ) -> Dict[str, str]:
        """
        Saves train, val, test sets and the trained preprocessor pipeline.
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        prep_p = Path(preprocessor_path)
        prep_p.parent.mkdir(parents=True, exist_ok=True)

        train_path = out_dir / "train.csv"
        val_path = out_dir / "val.csv"
        test_path = out_dir / "test.csv"
        cleaned_path = out_dir / "cleaned_air_quality.csv"

        pipeline_output["train_df"].to_csv(train_path, index=False)
        pipeline_output["val_df"].to_csv(val_path, index=False)
        pipeline_output["test_df"].to_csv(test_path, index=False)
        pipeline_output["cleaned_df"].to_csv(cleaned_path, index=False)

        # Save scikit-learn preprocessor pipeline
        joblib.dump(pipeline_output["preprocessor"], prep_p)

        return {
            "train_file": str(train_path),
            "val_file": str(val_path),
            "test_file": str(test_path),
            "cleaned_file": str(cleaned_path),
            "preprocessor_file": str(prep_p),
        }

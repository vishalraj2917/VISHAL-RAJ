from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional, Union
import pandas as pd
import numpy as np
import joblib

FEATURE_COLUMNS = [
    "pm25",
    "pm10",
    "co",
    "no2",
    "so2",
    "o3",
    "temperature",
    "humidity",
    "wind_speed",
    "pressure",
    "hour",
    "day",
    "month",
    "day_of_week",
    "is_weekend",
    "hour_sin",
    "hour_cos",
    "month_sin",
    "month_cos",
    "pm_ratio",
    "temp_humidity_idx",
]

TARGET_COLUMN = "aqi"


def resolve_project_path(rel_path: Union[str, Path]) -> Path:
    """
    Resolves relative path checking root workspace and backend directories.
    """
    p = Path(rel_path)
    if p.is_absolute() and p.exists():
        return p
    candidates = [
        Path.cwd() / p,
        Path.cwd() / "backend" / p,
        Path(__file__).resolve().parent.parent / p,
        Path(__file__).resolve().parent.parent / "backend" / p,
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def load_datasets(
    train_path: str = "data/processed/train.csv",
    val_path: str = "data/processed/val.csv",
    test_path: str = "data/processed/test.csv",
    target_col: str = TARGET_COLUMN,
    feature_cols: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, List[str], str]:
    """
    Loads train, val, test CSV datasets and extracts features & target.
    """
    p_train = resolve_project_path(train_path)
    p_val = resolve_project_path(val_path)
    p_test = resolve_project_path(test_path)

    if not p_train.exists():
        raise FileNotFoundError(f"Train dataset not found at: {p_train}")
    if not p_val.exists():
        raise FileNotFoundError(f"Validation dataset not found at: {p_val}")
    if not p_test.exists():
        raise FileNotFoundError(f"Test dataset not found at: {p_test}")

    train_df = pd.read_csv(p_train)
    val_df = pd.read_csv(p_val)
    test_df = pd.read_csv(p_test)

    # Detect / verify target column
    if target_col not in train_df.columns:
        # Check case-insensitive
        matches = [c for c in train_df.columns if c.lower() == target_col.lower()]
        if matches:
            target_col = matches[0]
        else:
            raise ValueError(f"Target column '{target_col}' not found in dataset columns: {list(train_df.columns)}")

    # Detect features
    if feature_cols is None:
        feature_cols = [f for f in FEATURE_COLUMNS if f in train_df.columns]
    else:
        feature_cols = [f for f in feature_cols if f in train_df.columns]

    if not feature_cols:
        raise ValueError("No matching feature columns found in dataset.")

    return train_df, val_df, test_df, feature_cols, target_col

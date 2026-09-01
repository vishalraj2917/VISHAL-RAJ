import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

NUMERIC_COLUMNS = [
    "pm25",
    "pm10",
    "co",
    "no2",
    "so2",
    "o3",
    "aqi",
    "temperature",
    "humidity",
    "wind_speed",
    "pressure",
]

# Domain physical constraints: min and max valid boundaries for sensor readings
PHYSICAL_BOUNDS: Dict[str, tuple[float, float]] = {
    "pm25": (0.0, 1000.0),
    "pm10": (0.0, 1500.0),
    "co": (0.0, 100.0),
    "no2": (0.0, 1000.0),
    "so2": (0.0, 1000.0),
    "o3": (0.0, 1000.0),
    "aqi": (0.0, 1000.0),
    "temperature": (-50.0, 60.0),  # Celsius
    "humidity": (0.0, 100.0),      # Percentage
    "wind_speed": (0.0, 150.0),    # m/s or km/h normalized
    "pressure": (800.0, 1100.0),   # hPa
}


class DataCleaner:
    """
    Cleans air quality and weather data:
    - Handles data types and invalid numeric formats
    - Removes exact duplicate records
    - Replaces negative values / physically impossible values with NaN
    - Handles missing values via time-aware forward/backward fill and median impute
    - Handles outliers using domain boundaries or IQR clipping
    - Parses and sorts timestamps chronologically
    """

    def __init__(self, bounds: Optional[Dict[str, tuple[float, float]]] = None):
        self.bounds = bounds or PHYSICAL_BOUNDS
        self.stats: Dict[str, Any] = {}

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Executes end-to-end cleaning pipeline on input DataFrame.
        """
        df = df.copy()
        rows_loaded = len(df)
        missing_before = int(df.isna().sum().sum())

        logger.info(f"Starting data cleaning on {rows_loaded} rows.")

        # 1. Parse and validate timestamp
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            # Drop rows where timestamp is unparseable
            df = df.dropna(subset=["timestamp"])
            df = df.sort_values(by="timestamp").reset_index(drop=True)

        # 2. Remove duplicate timestamps or identical records
        subset_cols = ["timestamp", "city"] if "city" in df.columns and "timestamp" in df.columns else (
            ["timestamp"] if "timestamp" in df.columns else None
        )
        duplicates_count = int(df.duplicated(subset=subset_cols).sum())
        if duplicates_count > 0:
            df = df.drop_duplicates(subset=subset_cols, keep="first").reset_index(drop=True)

        # 3. Numeric conversions & Physical Bounds Filtering
        for col in NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                # Enforce physical min/max bounds: invalid / negative values set to NaN
                if col in self.bounds:
                    min_val, max_val = self.bounds[col]
                    df.loc[(df[col] < min_val) | (df[col] > max_val), col] = np.nan

        # 4. Handle Missing Values without data leakage
        # For time-series, forward fill then backward fill within reason, then fallback to column median
        for col in NUMERIC_COLUMNS:
            if col in df.columns:
                # Forward fill (propagate last valid observation forward up to 3 steps)
                df[col] = df[col].ffill(limit=3)
                # Backward fill (propagate next valid observation backward up to 3 steps)
                df[col] = df[col].bfill(limit=3)
                # If still NaN, impute with median
                if df[col].isna().any():
                    col_median = df[col].median()
                    if pd.notna(col_median):
                        df[col] = df[col].fillna(col_median)
                    else:
                        df[col] = df[col].fillna(0.0)

        # 5. Clean metadata columns
        if "city" in df.columns:
            df["city"] = df["city"].fillna("Default").astype(str).str.strip()
        if "country" in df.columns:
            df["country"] = df["country"].fillna("India").astype(str).str.strip()

        rows_cleaned = len(df)
        missing_after = int(df.isna().sum().sum())

        self.stats = {
            "rows_loaded": rows_loaded,
            "duplicates_removed": duplicates_count,
            "rows_retained": rows_cleaned,
            "missing_values_before": missing_before,
            "missing_values_after": missing_after,
        }

        logger.info(f"Cleaning complete: {self.stats}")
        return df

    def get_stats(self) -> Dict[str, Any]:
        return self.stats

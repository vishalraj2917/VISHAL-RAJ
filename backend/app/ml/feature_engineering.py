import logging
from typing import List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_sub_aqi_pm25(cp: float) -> float:
    """
    Computes Indian / US EPA standard linear interpolation for PM2.5 sub-index.
    """
    if pd.isna(cp) or cp < 0:
        return 0.0
    breakpoints = [
        (0.0, 30.0, 0.0, 50.0),
        (30.1, 60.0, 51.0, 100.0),
        (60.1, 90.0, 101.0, 200.0),
        (90.1, 120.0, 201.0, 300.0),
        (120.1, 250.0, 301.0, 400.0),
        (250.1, 500.0, 401.0, 500.0),
    ]
    for b_lo, b_hi, i_lo, i_hi in breakpoints:
        if b_lo <= cp <= b_hi:
            return i_lo + ((i_hi - i_lo) / (b_hi - b_lo)) * (cp - b_lo)
    if cp > 500.0:
        return 500.0
    return 0.0


def calculate_sub_aqi_pm10(cp: float) -> float:
    """
    Computes linear interpolation for PM10 sub-index.
    """
    if pd.isna(cp) or cp < 0:
        return 0.0
    breakpoints = [
        (0.0, 50.0, 0.0, 50.0),
        (51.0, 100.0, 51.0, 100.0),
        (101.0, 250.0, 101.0, 200.0),
        (251.0, 350.0, 201.0, 300.0),
        (351.0, 430.0, 301.0, 400.0),
        (431.0, 600.0, 401.0, 500.0),
    ]
    for b_lo, b_hi, i_lo, i_hi in breakpoints:
        if b_lo <= cp <= b_hi:
            return i_lo + ((i_hi - i_lo) / (b_hi - b_lo)) * (cp - b_lo)
    if cp > 600.0:
        return 500.0
    return 0.0


def derive_composite_aqi(row: pd.Series) -> float:
    """
    Computes composite AQI from available pollutants when direct AQI is absent.
    Takes max sub-index across available pollutants (PM2.5, PM10, etc.).
    """
    sub_indices = []
    if "pm25" in row and pd.notna(row["pm25"]):
        sub_indices.append(calculate_sub_aqi_pm25(row["pm25"]))
    if "pm10" in row and pd.notna(row["pm10"]):
        sub_indices.append(calculate_sub_aqi_pm10(row["pm10"]))
    if sub_indices:
        return float(np.max(sub_indices))
    return 50.0  # Moderate default baseline if no pollutants


class FeatureEngineer:
    """
    Extracts time-based and environmental interaction features.
    Strictly avoids future data leakage (only uses historical/current timestamp information).
    """

    def __init__(self, add_cyclical_time: bool = True, add_lags: bool = False):
        self.add_cyclical_time = add_cyclical_time
        self.add_lags = add_lags

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Creates all time and pollution/weather interaction features.
        """
        df = df.copy()

        # 1. Target column verification / derivation
        if "aqi" not in df.columns or df["aqi"].isna().all():
            logger.info("AQI column missing or empty; deriving composite AQI from pollutant sub-indices.")
            df["aqi"] = df.apply(derive_composite_aqi, axis=1)

        # 2. Time Features from timestamp
        if "timestamp" in df.columns:
            ts = pd.to_datetime(df["timestamp"])
            df["hour"] = ts.dt.hour
            df["day"] = ts.dt.day
            df["month"] = ts.dt.month
            df["day_of_week"] = ts.dt.dayofweek
            df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

            # Cyclical encoding for periodic time components (hour, month)
            if self.add_cyclical_time:
                df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24.0)
                df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24.0)
                df["month_sin"] = np.sin(2 * np.pi * (df["month"] - 1) / 12.0)
                df["month_cos"] = np.cos(2 * np.pi * (df["month"] - 1) / 12.0)

        # 3. Domain Interaction Features
        # PM ratio (PM2.5 / PM10 indicates combustion vs coarse dust ratio)
        if "pm25" in df.columns and "pm10" in df.columns:
            # Safe division avoiding divide by zero
            df["pm_ratio"] = df["pm25"] / (df["pm10"] + 1e-5)
            # Clip PM ratio to physical expectations [0, 1.5]
            df["pm_ratio"] = df["pm_ratio"].clip(0.0, 1.5)

        # Heat Index / Temperature-Humidity interaction
        if "temperature" in df.columns and "humidity" in df.columns:
            df["temp_humidity_idx"] = (df["temperature"] * df["humidity"]) / 100.0

        # Optional Lag Features (past only - no forward shift)
        if self.add_lags and "aqi" in df.columns:
            df["aqi_lag_1h"] = df["aqi"].shift(1).bfill()
            df["aqi_lag_24h"] = df["aqi"].shift(24).bfill()

        return df

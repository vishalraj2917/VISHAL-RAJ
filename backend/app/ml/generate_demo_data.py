"""
Reference & Demo Dataset Generator (Clearly Labeled Demo Data)
Generates realistic 1-year hourly historical air-quality & weather records for testing
the preprocessing and ML pipeline.
"""
from pathlib import Path
import numpy as np
import pandas as pd


def generate_demo_dataset(
    output_path: str = "data/sample/demo_air_quality_weather.csv",
    n_days: int = 180,
    city: str = "Bengaluru",
    state: str = "Karnataka",
    country: str = "India",
    latitude: float = 12.9716,
    longitude: float = 77.5946,
) -> Path:
    """
    Generates a continuous time-series demo dataset containing:
    - Diurnal (day/night) cycles
    - Seasonal variations
    - Weather patterns (temp, humidity, wind, pressure)
    - Pollutants (PM2.5, PM10, CO, NO2, SO2, O3, AQI)
    - Realistic sensor noise and occasional missing values / duplicates for testing cleaner robustness
    """
    np.random.seed(42)
    start_date = pd.Timestamp("2025-01-01 00:00:00")
    total_hours = n_days * 24
    timestamps = [start_date + pd.Timedelta(hours=i) for i in range(total_hours)]

    records = []
    for i, ts in enumerate(timestamps):
        hour = ts.hour
        month = ts.month

        # Base temperature: warmer at 2pm (hour 14), cooler at 5am
        temp_diurnal = 5.0 * np.sin(2 * np.pi * (hour - 8) / 24.0)
        temp_seasonal = 3.0 * np.sin(2 * np.pi * (month - 1) / 12.0)
        temp = 24.0 + temp_diurnal + temp_seasonal + np.random.normal(0, 1.0)

        # Humidity: inverse to temp
        humidity = 65.0 - (temp_diurnal * 2.5) + np.random.normal(0, 3.0)
        humidity = np.clip(humidity, 20.0, 98.0)

        # Wind speed: higher in afternoon
        wind_speed = 3.5 + 1.5 * np.sin(2 * np.pi * (hour - 10) / 24.0) + np.random.normal(0, 0.8)
        wind_speed = max(0.5, wind_speed)

        # Pressure (hPa)
        pressure = 1012.0 + np.sin(2 * np.pi * (hour - 9) / 12.0) + np.random.normal(0, 0.5)

        # Traffic rush hour spikes at 8-10 AM and 6-9 PM
        traffic_peak = 1.0
        if 8 <= hour <= 10 or 18 <= hour <= 21:
            traffic_peak = 2.2

        # Inversion effect (winter + nighttime traps pollutants)
        inversion = 1.4 if (month in [11, 12, 1, 2] and (hour <= 7 or hour >= 22)) else 1.0

        # Pollutant levels with realistic atmospheric correlation
        pm25 = (28.0 * traffic_peak * inversion / (wind_speed * 0.3 + 0.7)) + np.random.normal(0, 4.0)
        pm25 = max(5.0, pm25)

        pm10 = pm25 * np.random.uniform(1.4, 2.0) + np.random.normal(0, 8.0)
        pm10 = max(10.0, pm10)

        co = (0.6 * traffic_peak) + np.random.normal(0, 0.1)
        co = max(0.1, co)

        no2 = (22.0 * traffic_peak) + np.random.normal(0, 3.0)
        no2 = max(5.0, no2)

        so2 = 12.0 + np.random.normal(0, 2.0)
        so2 = max(2.0, so2)

        # Ozone peaks during midday sunshine
        o3 = (35.0 * max(0.0, np.sin(np.pi * (hour - 6) / 12.0))) + np.random.normal(0, 3.0)
        o3 = max(2.0, o3)

        # Indian National Air Quality Index calculation approximation for PM2.5 / PM10
        aqi_val = max(pm25 * 1.5, pm10 * 0.8)

        records.append({
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "city": city,
            "state": state,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "pm25": round(pm25, 2),
            "pm10": round(pm10, 2),
            "co": round(co, 2),
            "no2": round(no2, 2),
            "so2": round(so2, 2),
            "o3": round(o3, 2),
            "aqi": round(aqi_val, 2),
            "temperature": round(temp, 2),
            "humidity": round(humidity, 2),
            "wind_speed": round(wind_speed, 2),
            "pressure": round(pressure, 2),
        })

    df = pd.DataFrame(records)

    # Introduce a few realistic data cleaning scenarios:
    # 1. 2% missing values in PM2.5 / Temperature
    mask_nan = np.random.rand(len(df)) < 0.02
    df.loc[mask_nan, "pm25"] = np.nan

    mask_nan_temp = np.random.rand(len(df)) < 0.015
    df.loc[mask_nan_temp, "temperature"] = np.nan

    # 2. 5 duplicate rows
    duplicates = df.iloc[10:15].copy()
    df = pd.concat([df, duplicates], ignore_index=True)

    # 3. 3 outlier/sensor error rows (-99.0 reading)
    df.loc[50, "pm25"] = -99.0
    df.loc[100, "wind_speed"] = -10.0

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Demo dataset created with {len(df)} rows at: {out_path.resolve()}")
    return out_path


if __name__ == "__main__":
    generate_demo_dataset()

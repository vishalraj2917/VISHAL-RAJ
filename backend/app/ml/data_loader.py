import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any, List
import pandas as pd

logger = logging.getLogger(__name__)

# Standard column mapping to harmonize diverse CSV sources
STANDARD_COLUMN_MAP: Dict[str, str] = {
    # Timestamps
    "timestamp": "timestamp",
    "datetime": "timestamp",
    "date": "timestamp",
    "time": "timestamp",
    "date_time": "timestamp",
    "from date": "timestamp",
    "to date": "timestamp",
    # Pollutants
    "pm2.5": "pm25",
    "pm25": "pm25",
    "pm2_5": "pm25",
    "pm10": "pm10",
    "co": "co",
    "carbon_monoxide": "co",
    "no2": "no2",
    "nitrogen_dioxide": "no2",
    "so2": "so2",
    "sulfur_dioxide": "so2",
    "o3": "o3",
    "ozone": "o3",
    "aqi": "aqi",
    "air_quality_index": "aqi",
    # Weather
    "temperature": "temperature",
    "temp": "temperature",
    "humidity": "humidity",
    "rh": "humidity",
    "relative_humidity": "humidity",
    "wind_speed": "wind_speed",
    "windspeed": "wind_speed",
    "ws": "wind_speed",
    "pressure": "pressure",
    "atmospheric_pressure": "pressure",
    "at": "pressure",
    "barometer": "pressure",
    # Metadata
    "city": "city",
    "location": "city",
    "station": "city",
    "state": "state",
    "country": "country",
    "latitude": "latitude",
    "lat": "latitude",
    "longitude": "longitude",
    "lon": "longitude",
    "lng": "longitude",
}


class DataLoader:
    """
    Flexible data loader for historical air quality and weather datasets.
    Supports CSV files, dictionary records, and future live API integrations.
    """

    def __init__(self, column_map: Optional[Dict[str, str]] = None):
        self.column_map = {**STANDARD_COLUMN_MAP, **(column_map or {})}

    def load_csv(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """
        Loads dataset from a CSV file and normalizes column headers.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found at: {path}")

        logger.info(f"Loading CSV dataset from: {path}")
        df = pd.read_csv(path)
        return self.normalize_columns(df)

    def load_from_records(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Loads dataset from list of dictionaries / JSON records.
        """
        df = pd.DataFrame(records)
        return self.normalize_columns(df)

    def normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardizes column names by stripping spaces, lowering cases,
        and mapping known aliases to the project standard.
        """
        df = df.copy()
        renamed = {}
        for col in df.columns:
            clean_name = str(col).strip().lower().replace("-", "_").replace(" ", "_")
            if clean_name in self.column_map:
                renamed[col] = self.column_map[clean_name]
            elif str(col).strip().lower() in self.column_map:
                renamed[col] = self.column_map[str(col).strip().lower()]
            else:
                renamed[col] = clean_name

        df.rename(columns=renamed, inplace=True)
        return df

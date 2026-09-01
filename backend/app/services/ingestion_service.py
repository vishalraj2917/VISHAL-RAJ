import logging
from typing import Dict, Any, List
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.models import Location, AirQuality, Weather

logger = logging.getLogger(__name__)


class DataIngestionService:
    """
    Service to persist cleaned historical or ingested air quality & weather
    records into PostgreSQL using existing SQLAlchemy models.
    Prevents duplicates by checking existing timestamp + location records.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_location(
        self,
        city: str,
        state: str = None,
        country: str = "India",
        latitude: float = 0.0,
        longitude: float = 0.0,
    ) -> Location:
        """
        Fetches existing location record or creates a new one.
        """
        loc = (
            self.db.query(Location)
            .filter(Location.city == city, Location.country == country)
            .first()
        )
        if not loc:
            loc = Location(
                city=city,
                state=state,
                country=country,
                latitude=latitude,
                longitude=longitude,
            )
            self.db.add(loc)
            self.db.commit()
            self.db.refresh(loc)
            logger.info(f"Created new Location record: {city}, {country} (ID: {loc.id})")
        return loc

    def ingest_cleaned_dataframe(
        self, df: pd.DataFrame, batch_size: int = 500
    ) -> Dict[str, int]:
        """
        Ingests a cleaned pandas DataFrame into air_quality and weather tables.
        Avoids duplicate entries for the same timestamp and location.
        """
        if df.empty:
            return {"air_quality_inserted": 0, "weather_inserted": 0, "skipped": 0}

        # Determine location
        city = df["city"].iloc[0] if "city" in df.columns else "Bengaluru"
        state = df["state"].iloc[0] if "state" in df.columns else "Karnataka"
        country = df["country"].iloc[0] if "country" in df.columns else "India"
        lat = float(df["latitude"].iloc[0]) if "latitude" in df.columns else 12.9716
        lon = float(df["longitude"].iloc[0]) if "longitude" in df.columns else 77.5946

        location = self.get_or_create_location(city, state, country, lat, lon)

        # Get existing timestamps to prevent duplicates
        existing_aq_ts = set(
            ts[0]
            for ts in self.db.query(AirQuality.timestamp)
            .filter(AirQuality.location_id == location.id)
            .all()
        )
        existing_weather_ts = set(
            ts[0]
            for ts in self.db.query(Weather.timestamp)
            .filter(Weather.location_id == location.id)
            .all()
        )

        aq_records_to_insert = []
        weather_records_to_insert = []
        skipped = 0

        for _, row in df.iterrows():
            ts = pd.to_datetime(row["timestamp"]).to_pydatetime()

            # Air quality record
            if ts not in existing_aq_ts and "aqi" in row:
                aq_rec = AirQuality(
                    location_id=location.id,
                    timestamp=ts,
                    pm25=float(row["pm25"]) if "pm25" in row and pd.notna(row["pm25"]) else None,
                    pm10=float(row["pm10"]) if "pm10" in row and pd.notna(row["pm10"]) else None,
                    co=float(row["co"]) if "co" in row and pd.notna(row["co"]) else None,
                    no2=float(row["no2"]) if "no2" in row and pd.notna(row["no2"]) else None,
                    so2=float(row["so2"]) if "so2" in row and pd.notna(row["so2"]) else None,
                    o3=float(row["o3"]) if "o3" in row and pd.notna(row["o3"]) else None,
                    aqi=float(row["aqi"]) if pd.notna(row["aqi"]) else 0.0,
                )
                aq_records_to_insert.append(aq_rec)
                existing_aq_ts.add(ts)

            # Weather record
            if ts not in existing_weather_ts and (
                "temperature" in row or "humidity" in row or "wind_speed" in row
            ):
                weather_rec = Weather(
                    location_id=location.id,
                    timestamp=ts,
                    temperature=float(row["temperature"]) if "temperature" in row and pd.notna(row["temperature"]) else None,
                    humidity=float(row["humidity"]) if "humidity" in row and pd.notna(row["humidity"]) else None,
                    wind_speed=float(row["wind_speed"]) if "wind_speed" in row and pd.notna(row["wind_speed"]) else None,
                    pressure=float(row["pressure"]) if "pressure" in row and pd.notna(row["pressure"]) else None,
                )
                weather_records_to_insert.append(weather_rec)
                existing_weather_ts.add(ts)

        # Batch insert
        if aq_records_to_insert:
            self.db.bulk_save_objects(aq_records_to_insert)
        if weather_records_to_insert:
            self.db.bulk_save_objects(weather_records_to_insert)

        self.db.commit()

        logger.info(
            f"Database Ingestion: AQ inserted={len(aq_records_to_insert)}, "
            f"Weather inserted={len(weather_records_to_insert)}"
        )

        return {
            "air_quality_inserted": len(aq_records_to_insert),
            "weather_inserted": len(weather_records_to_insert),
            "skipped": skipped,
        }

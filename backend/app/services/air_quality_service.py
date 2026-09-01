import logging
from typing import Dict, Any, Optional
import httpx

from app.config import settings
from app.services.cache_service import live_data_cache

logger = logging.getLogger(__name__)


class AirQualityService:
    """
    Client for fetching and normalizing real-time pollutant measurements by geographic coordinates.
    Integrates with Open-Meteo Air Quality API.
    """

    def __init__(
        self,
        base_url: str = settings.AIR_QUALITY_API_BASE_URL,
        timeout: float = settings.EXTERNAL_API_TIMEOUT_SECONDS,
        api_key: Optional[str] = (settings.AIR_QUALITY_API_KEY or settings.AQI_API_KEY),
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.api_key = api_key

    async def fetch_current_air_quality(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Fetches current pollutant levels: PM2.5, PM10, CO, NO2, SO2, O3.
        Normalizes units to match project standard:
        - PM2.5, PM10, NO2, SO2, O3: µg/m³
        - CO: mg/m³ (converted from µg/m³ if returned as µg/m³)
        """
        cached = live_data_cache.get(latitude, longitude, "air_quality")
        if cached is not None:
            logger.debug(f"Returning cached air quality data for ({latitude}, {longitude})")
            return cached

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone",
            "timezone": "auto",
        }
        if self.api_key:
            params["apikey"] = self.api_key

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)

                if response.status_code == 400:
                    raise ValueError(f"Invalid coordinate parameters: {response.text}")
                if response.status_code == 401 or response.status_code == 403:
                    raise PermissionError("Air Quality API authentication error.")
                if response.status_code == 429:
                    raise RuntimeError("Air Quality API rate limit exceeded.")

                response.raise_for_status()
                data = response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Air Quality API timeout for ({latitude}, {longitude}): {e}")
            raise TimeoutError("Air Quality data provider timed out.") from e
        except httpx.RequestError as e:
            logger.error(f"Air Quality API connection error: {e}")
            raise ConnectionError("Could not connect to air quality data provider.") from e

        # Parse & normalize
        current = data.get("current", {})
        current_units = data.get("current_units", {})
        if not current:
            raise ValueError("No current air quality data in provider response.")

        pm25 = current.get("pm2_5")
        pm10 = current.get("pm10")
        co = current.get("carbon_monoxide")
        no2 = current.get("nitrogen_dioxide")
        so2 = current.get("sulphur_dioxide")
        o3 = current.get("ozone")
        timestamp_str = current.get("time")

        if any(v is None for v in [pm25, pm10, co, no2, so2, o3]):
            raise ValueError("Missing critical pollutant metrics in provider response.")

        pm25_val = float(pm25)
        pm10_val = float(pm10)
        co_raw = float(co)
        no2_val = float(no2)
        so2_val = float(so2)
        o3_val = float(o3)

        # Convert CO from µg/m³ to mg/m³ if reported in µg/m³
        co_unit = current_units.get("carbon_monoxide", "μg/m³")
        if "μg" in co_unit or "ug" in co_unit:
            co_val = round(co_raw / 1000.0, 3)
        else:
            co_val = round(co_raw, 3)

        normalized_aq = {
            "pm25": pm25_val,
            "pm10": pm10_val,
            "co": co_val,
            "no2": no2_val,
            "so2": so2_val,
            "o3": o3_val,
            "timestamp": timestamp_str,
            "timezone": data.get("timezone", "UTC"),
        }

        # Cache valid result
        live_data_cache.set(latitude, longitude, "air_quality", normalized_aq)
        return normalized_aq

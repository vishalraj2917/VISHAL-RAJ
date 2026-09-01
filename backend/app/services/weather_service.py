import logging
from typing import Dict, Any, Optional
import httpx

from app.config import settings
from app.services.cache_service import live_data_cache

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Client for fetching and normalizing real-time weather data by geographic coordinates.
    Integrates with Open-Meteo Weather Forecast API.
    """

    def __init__(
        self,
        base_url: str = settings.WEATHER_API_BASE_URL,
        timeout: float = settings.EXTERNAL_API_TIMEOUT_SECONDS,
        api_key: Optional[str] = settings.WEATHER_API_KEY,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.api_key = api_key

    async def fetch_current_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Fetches current weather parameters: temperature (°C), relative humidity (%),
        wind speed (km/h), and surface pressure (hPa).
        """
        cached = live_data_cache.get(latitude, longitude, "weather")
        if cached is not None:
            logger.debug(f"Returning cached weather data for ({latitude}, {longitude})")
            return cached

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,surface_pressure",
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
                    raise PermissionError("Weather API authentication error.")
                if response.status_code == 429:
                    raise RuntimeError("Weather API rate limit exceeded.")

                response.raise_for_status()
                data = response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Weather API timeout for ({latitude}, {longitude}): {e}")
            raise TimeoutError("Weather data provider timed out.") from e
        except httpx.RequestError as e:
            logger.error(f"Weather API connection error: {e}")
            raise ConnectionError("Could not connect to weather data provider.") from e

        # Parse & normalize
        current = data.get("current", {})
        if not current:
            raise ValueError("No current weather data in provider response.")

        temperature = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind_speed = current.get("wind_speed_10m")
        pressure = current.get("surface_pressure")
        timestamp_str = current.get("time")

        if any(v is None for v in [temperature, humidity, wind_speed, pressure]):
            raise ValueError("Missing critical meteorological variables in provider response.")

        normalized_weather = {
            "temperature": float(temperature),
            "humidity": float(humidity),
            "wind_speed": float(wind_speed),
            "pressure": float(pressure),
            "timestamp": timestamp_str,
            "timezone": data.get("timezone", "UTC"),
        }

        # Cache valid result
        live_data_cache.set(latitude, longitude, "weather", normalized_weather)
        return normalized_weather

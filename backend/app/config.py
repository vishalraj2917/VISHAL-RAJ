import os
from typing import Optional, List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"  # "development", "production", "testing"
    LOG_LEVEL: str = "INFO"           # "DEBUG", "INFO", "WARNING", "ERROR"

    DATABASE_URL: str = 'postgresql://postgres:postgres@localhost:5432/ai_air_quality'
    SECRET_KEY: str = 'your-super-secret-jwt-key-change-this-in-production'
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # API documentation exposure (Can be disabled in production)
    ENABLE_DOCS: bool = True

    # External Provider APIs
    AQI_API_KEY: Optional[str] = None
    WEATHER_API_KEY: Optional[str] = None
    AIR_QUALITY_API_KEY: Optional[str] = None
    AI_API_KEY: Optional[str] = None
    AI_PROVIDER: str = "gemini"  # Supported: "gemini", "openai", "local"
    AI_MODEL: str = "gemini-1.5-flash"

    # Open-Meteo endpoint configurations (Defaults to free tier public API)
    WEATHER_API_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"
    AIR_QUALITY_API_BASE_URL: str = "https://air-quality-api.open-meteo.com/v1/air-quality"
    EXTERNAL_API_TIMEOUT_SECONDS: float = 10.0
    LIVE_DATA_CACHE_TTL_SECONDS: int = 300  # 5 minutes TTL

    # AI Feature parameters
    AI_MAX_INPUT_CHARS: int = 2000
    AI_MAX_OUTPUT_TOKENS: int = 1000
    AI_REQUEST_TIMEOUT_SECONDS: float = 15.0

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=('.env', 'backend/.env', '../.env'),
        env_file_encoding='utf-8',
        extra='ignore'
    )


settings = Settings()

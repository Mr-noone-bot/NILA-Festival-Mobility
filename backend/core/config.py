"""
NILA Core Configuration
Settings management for the festival mobility and crowd management system.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "NILA Festival Mobility & Crowd Management System"
    API_V1_PREFIX: str = "/api"
    DEBUG: bool = False
    
    # Network / Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # External APIs (Configurable via .env)
    GEMINI_API_KEY: str = ""
    OSRM_BACKEND_URL: str = "https://router.project-osrm.org"
    OSRM_TIMEOUT_SECONDS: float = 3.5
    ROUTE_CACHE_TTL_SECONDS: int = 3600
    
    # Operational & Simulation Defaults
    DEFAULT_BUS_CAPACITY: int = 50
    ALLOW_SYNTHETIC_CAPACITY_FALLBACK: bool = True
    FALLBACK_AVERAGE_SPEED_KMH: float = 20.0
    DATA_DIR: str = "data"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

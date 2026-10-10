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
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

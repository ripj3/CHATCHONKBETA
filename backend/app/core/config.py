"""
Application Configuration Management

This module uses Pydantic's settings management to load and validate
environment variables for the ChatChonk application.

It centralizes all configuration, making it easy to manage and access
settings throughout the backend.

Author: Rip Jonesy
"""

import os
from typing import List, Optional

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings, loaded from environment variables."""

    # General
    PROJECT_NAME: str = "ChatChonk"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_HOST: str = "0.0.0.0"
    PORT: int = 8080
    API_V1_STR: str = "/api"
    CHONK_SECRET_KEY: str

    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Create a singleton settings instance
settings = Settings()

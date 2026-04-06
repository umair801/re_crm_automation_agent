"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """All application settings loaded from .env file."""

    # OpenAI
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")

    # GoHighLevel
    GHL_API_KEY: str = Field(..., description="GHL private API key")
    GHL_LOCATION_ID: str = Field(..., description="GHL location/sub-account ID")
    GHL_PIPELINE_ID: str = Field(..., description="GHL pipeline ID")
    GHL_WEBHOOK_SECRET: str = Field(..., description="GHL webhook secret for signature verification")

    # Supabase
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_KEY: str = Field(..., description="Supabase anon/service key")

    # App
    APP_ENV: str = Field(default="development")
    APP_HOST: str = Field(default="0.0.0.0")
    APP_PORT: int = Field(default=8000)
    LOG_LEVEL: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
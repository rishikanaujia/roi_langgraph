"""
API Configuration

Reads configuration from environment variables with sensible defaults.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """API settings from environment variables."""

    # API Configuration
    api_title: str = Field(
        default="Phase 1 Rankings API",
        description="API title"
    )

    api_version: str = Field(
        default="1.0.0",
        description="API version"
    )

    api_description: str = Field(
        default="Multi-agent renewable energy country ranking system",
        description="API description"
    )

    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )

    port: int = Field(
        default=8000,
        description="Server port"
    )

    reload: bool = Field(
        default=True,
        description="Auto-reload on code changes (dev only)"
    )

    log_level: str = Field(
        default="info",
        description="Logging level"
    )

    # CORS Configuration
    cors_origins: list = Field(
        default=["*"],
        description="Allowed CORS origins"
    )

    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS"
    )

    # OpenAI Configuration
    openai_api_key: str = Field(
        ...,
        description="OpenAI API key (required)"
    )

    openai_model: str = Field(
        default="gpt-4o",
        description="OpenAI model to use"
    )

    # Job Configuration
    max_countries: int = Field(
        default=15,
        ge=2,
        le=20,
        description="Maximum countries per job"
    )

    min_countries: int = Field(
        default=2,
        ge=2,
        description="Minimum countries per job"
    )

    default_peer_rankers: int = Field(
        default=3,
        ge=2,
        le=5,
        description="Default number of peer rankers"
    )

    max_peer_rankers: int = Field(
        default=5,
        ge=2,
        le=10,
        description="Maximum peer rankers per job"
    )

    job_timeout_seconds: int = Field(
        default=300,
        ge=60,
        description="Maximum job execution time"
    )

    # Storage Configuration
    reports_dir: str = Field(
        default="reports",
        description="Directory for generated reports"
    )

    storage_backend: str = Field(
        default="memory",
        description="Storage backend (memory|redis)"
    )

    redis_url: Optional[str] = Field(
        default=None,
        description="Redis URL (if using redis storage)"
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=False,
        description="Enable rate limiting"
    )

    rate_limit_per_minute: int = Field(
        default=10,
        description="Max requests per minute per IP"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance."""
    return settings


# Ensure reports directory exists
os.makedirs(settings.reports_dir, exist_ok=True)
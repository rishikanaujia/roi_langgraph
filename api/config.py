"""
API Configuration Management

Loads configuration from environment variables with sensible defaults.
Uses Pydantic BaseSettings for validation and type safety.

Environment variables can be set in .env file or system environment.
"""

import os
from typing import List, Optional
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via .env file or environment variables.
    Use uppercase with underscores (e.g., API_TITLE, OPENAI_API_KEY).
    """

    # ========================================================================
    # API Configuration
    # ========================================================================

    api_title: str = Field(
        default="Renewable Opportunity Identifier API",
        description="API title shown in documentation"
    )

    api_version: str = Field(
        default="1.0.0",
        description="API version"
    )

    api_description: str = Field(
        default="Multi-agent AI system for ranking renewable energy investment opportunities using LangGraph",
        description="API description shown in documentation"
    )

    environment: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )

    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )

    # ========================================================================
    # Server Configuration
    # ========================================================================

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
        description="Enable auto-reload for development"
    )

    log_level: str = Field(
        default="info",
        description="Logging level: debug, info, warning, error, critical"
    )

    workers: int = Field(
        default=1,
        description="Number of worker processes (production)"
    )

    # ========================================================================
    # CORS Configuration
    # ========================================================================

    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )

    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )

    cors_allow_methods: List[str] = Field(
        default=["*"],
        description="Allowed HTTP methods"
    )

    cors_allow_headers: List[str] = Field(
        default=["*"],
        description="Allowed HTTP headers"
    )

    # ========================================================================
    # OpenAI Configuration
    # ========================================================================

    openai_api_key: str = Field(
        default="",
        description="OpenAI API key (required)"
    )

    openai_model: str = Field(
        default="gpt-4o",
        description="OpenAI model to use for agents"
    )

    openai_temperature: float = Field(
        default=0.7,
        description="Temperature for OpenAI models"
    )

    openai_max_retries: int = Field(
        default=3,
        description="Maximum retries for OpenAI API calls"
    )

    openai_timeout: int = Field(
        default=120,
        description="Timeout for OpenAI API calls (seconds)"
    )

    # ========================================================================
    # Job Configuration
    # ========================================================================

    max_countries: int = Field(
        default=15,
        description="Maximum number of countries per job"
    )

    min_countries: int = Field(
        default=2,
        description="Minimum number of countries per job"
    )

    default_peer_rankers: int = Field(
        default=3,
        description="Default number of peer rankers"
    )

    max_peer_rankers: int = Field(
        default=5,
        description="Maximum number of peer rankers"
    )

    min_peer_rankers: int = Field(
        default=2,
        description="Minimum number of peer rankers"
    )

    job_timeout_seconds: int = Field(
        default=300,
        description="Maximum time for job execution (seconds)"
    )

    max_concurrent_jobs: int = Field(
        default=5,
        description="Maximum number of concurrent jobs"
    )

    # ========================================================================
    # Storage Configuration
    # ========================================================================

    storage_backend: str = Field(
        default="memory",
        description="Storage backend: memory or redis"
    )

    max_jobs_in_memory: int = Field(
        default=1000,
        description="Maximum jobs to keep in memory"
    )

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    redis_key_prefix: str = Field(
        default="roi:job:",
        description="Redis key prefix for jobs"
    )

    redis_ttl: int = Field(
        default=86400,
        description="Redis TTL for jobs (seconds, 24 hours default)"
    )

    redis_pool_size: int = Field(
        default=10,
        description="Redis connection pool size"
    )

    # ========================================================================
    # File System Configuration
    # ========================================================================

    reports_dir: str = Field(
        default="reports",
        description="Directory for generated reports"
    )

    data_dir: str = Field(
        default="data",
        description="Directory for research data"
    )

    logs_dir: str = Field(
        default="logs",
        description="Directory for log files"
    )

    temp_dir: str = Field(
        default="temp",
        description="Directory for temporary files"
    )

    # ========================================================================
    # Rate Limiting Configuration
    # ========================================================================

    rate_limit_enabled: bool = Field(
        default=False,
        description="Enable rate limiting"
    )

    rate_limit_per_minute: int = Field(
        default=60,
        description="Maximum requests per minute per IP"
    )

    rate_limit_per_hour: int = Field(
        default=1000,
        description="Maximum requests per hour per IP"
    )

    # ========================================================================
    # Monitoring & Observability
    # ========================================================================

    enable_metrics: bool = Field(
        default=False,
        description="Enable Prometheus metrics"
    )

    metrics_port: int = Field(
        default=9090,
        description="Port for metrics endpoint"
    )

    enable_tracing: bool = Field(
        default=False,
        description="Enable distributed tracing"
    )

    jaeger_agent_host: str = Field(
        default="localhost",
        description="Jaeger agent host"
    )

    jaeger_agent_port: int = Field(
        default=6831,
        description="Jaeger agent port"
    )

    # ========================================================================
    # Security Configuration
    # ========================================================================

    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens and encryption"
    )

    access_token_expire_minutes: int = Field(
        default=30,
        description="JWT access token expiration (minutes)"
    )

    enable_api_key_auth: bool = Field(
        default=False,
        description="Enable API key authentication"
    )

    api_keys: List[str] = Field(
        default=[],
        description="Valid API keys (comma-separated in env)"
    )

    # ========================================================================
    # Feature Flags
    # ========================================================================

    enable_langgraph: bool = Field(
        default=True,
        description="Use LangGraph workflow (vs legacy workflow)"
    )

    enable_phase2: bool = Field(
        default=False,
        description="Enable Phase 2 hot seat feature"
    )

    enable_checkpointing: bool = Field(
        default=False,
        description="Enable LangGraph checkpointing"
    )

    enable_streaming: bool = Field(
        default=False,
        description="Enable streaming responses"
    )

    enable_caching: bool = Field(
        default=True,
        description="Enable response caching"
    )

    cache_ttl_seconds: int = Field(
        default=3600,
        description="Cache TTL in seconds (1 hour default)"
    )

    # ========================================================================
    # Advanced Configuration
    # ========================================================================

    async_mode: bool = Field(
        default=True,
        description="Use async execution for workflows"
    )

    parallel_execution: bool = Field(
        default=True,
        description="Enable parallel agent execution"
    )

    max_parallel_agents: int = Field(
        default=10,
        description="Maximum parallel agent executions"
    )

    enable_mock_mode: bool = Field(
        default=False,
        description="Use mock data instead of real API calls (testing)"
    )

    # ========================================================================
    # Validators
    # ========================================================================

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        valid_envs = ['development', 'staging', 'production']
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ['debug', 'info', 'warning', 'error', 'critical']
        if v.lower() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.lower()

    @field_validator('storage_backend')
    @classmethod
    def validate_storage_backend(cls, v: str) -> str:
        """Validate storage backend."""
        valid_backends = ['memory', 'redis']
        if v.lower() not in valid_backends:
            raise ValueError(f"Storage backend must be one of: {valid_backends}")
        return v.lower()

    @field_validator('openai_api_key')
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Validate OpenAI API key is set."""
        if not v or v == "":
            raise ValueError(
                "OPENAI_API_KEY must be set. "
                "Get your key from https://platform.openai.com/api-keys"
            )
        return v

    @field_validator('min_countries', 'max_countries')
    @classmethod
    def validate_country_limits(cls, v: int) -> int:
        """Validate country limits are positive."""
        if v < 1:
            raise ValueError("Country limits must be positive")
        return v

    @field_validator('min_peer_rankers', 'max_peer_rankers')
    @classmethod
    def validate_peer_limits(cls, v: int) -> int:
        """Validate peer ranker limits."""
        if v < 1:
            raise ValueError("Peer ranker limits must be positive")
        return v

    # ========================================================================
    # Computed Properties
    # ========================================================================

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging."""
        return self.environment == "staging"

    @property
    def cors_settings(self) -> dict:
        """Get CORS settings as dict."""
        return {
            "allow_origins": self.cors_origins,
            "allow_credentials": self.cors_allow_credentials,
            "allow_methods": self.cors_allow_methods,
            "allow_headers": self.cors_allow_headers
        }

    @property
    def redis_config(self) -> dict:
        """Get Redis configuration as dict."""
        return {
            "url": self.redis_url,
            "key_prefix": self.redis_key_prefix,
            "ttl": self.redis_ttl,
            "pool_size": self.redis_pool_size
        }

    @property
    def openai_config(self) -> dict:
        """Get OpenAI configuration as dict."""
        return {
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "temperature": self.openai_temperature,
            "max_retries": self.openai_max_retries,
            "timeout": self.openai_timeout
        }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def ensure_directories(self):
        """Create required directories if they don't exist."""
        directories = [
            self.reports_dir,
            self.data_dir,
            self.logs_dir,
            self.temp_dir
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def print_config(self, hide_secrets: bool = True):
        """Print current configuration (for debugging)."""
        print("=" * 70)
        print("CONFIGURATION")
        print("=" * 70)

        config_dict = self.model_dump()

        # Hide sensitive values
        if hide_secrets:
            sensitive_keys = [
                'openai_api_key',
                'secret_key',
                'api_keys'
            ]
            for key in sensitive_keys:
                if key in config_dict and config_dict[key]:
                    config_dict[key] = "***HIDDEN***"

        # Print grouped by section
        sections = {
            "API": ['api_title', 'api_version', 'environment', 'debug'],
            "Server": ['host', 'port', 'workers', 'log_level'],
            "OpenAI": ['openai_model', 'openai_temperature', 'openai_api_key'],
            "Job Limits": ['min_countries', 'max_countries', 'min_peer_rankers', 'max_peer_rankers'],
            "Storage": ['storage_backend', 'redis_url', 'max_jobs_in_memory'],
            "Features": ['enable_langgraph', 'enable_phase2', 'enable_caching']
        }

        for section, keys in sections.items():
            print(f"\n{section}:")
            for key in keys:
                if key in config_dict:
                    value = config_dict[key]
                    print(f"  {key}: {value}")

        print("\n" + "=" * 70)

    # ========================================================================
    # Pydantic Config
    # ========================================================================

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env


# ============================================================================
# Singleton Pattern
# ============================================================================

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance (singleton pattern).

    Returns:
        Settings instance

    Example:
        >>> from api.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.api_title)
    """
    settings = Settings()

    # Ensure required directories exist
    settings.ensure_directories()

    return settings


# ============================================================================
# Environment-Specific Settings
# ============================================================================

def get_development_settings() -> Settings:
    """Get settings optimized for development."""
    return Settings(
        environment="development",
        debug=True,
        reload=True,
        log_level="debug",
        enable_mock_mode=True,
        storage_backend="memory"
    )


def get_production_settings() -> Settings:
    """Get settings optimized for production."""
    return Settings(
        environment="production",
        debug=False,
        reload=False,
        log_level="warning",
        workers=4,
        enable_mock_mode=False,
        storage_backend="redis",
        enable_metrics=True,
        enable_tracing=True,
        rate_limit_enabled=True
    )


def get_testing_settings() -> Settings:
    """Get settings optimized for testing."""
    return Settings(
        environment="development",
        debug=True,
        log_level="error",
        enable_mock_mode=True,
        storage_backend="memory",
        openai_api_key="test-key-not-used",
        job_timeout_seconds=10
    )


# ============================================================================
# Export
# ============================================================================

__all__ = [
    "Settings",
    "get_settings",
    "get_development_settings",
    "get_production_settings",
    "get_testing_settings"
]
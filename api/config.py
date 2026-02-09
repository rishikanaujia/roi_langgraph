"""
API Configuration Management

Loads configuration from environment variables with sensible defaults.
Uses Pydantic BaseSettings for validation and type safety.

Environment variables can be set in .env file or system environment.

Updated: 2024-12-08 - Refactored for Azure OpenAI support
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
    Use uppercase with underscores (e.g., API_TITLE, AZURE_OPENAI_KEY).
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
        default="Multi-agent AI system for ranking renewable energy investment opportunities using LangGraph and Azure OpenAI",
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
    # Azure OpenAI Configuration
    # ========================================================================

    azure_openai_key: str = Field(
        default="",
        description="Azure OpenAI API key (required)"
    )

    azure_openai_endpoint: str = Field(
        default="https://sparkapi.spglobal.com/v1/sparkassist",
        description="Azure OpenAI endpoint URL"
    )

    azure_openai_deployment: str = Field(
        default="gpt-4o-mini",
        description="Azure OpenAI deployment name"
    )

    azure_openai_api_version: str = Field(
        default="2024-02-01",
        description="Azure OpenAI API version"
    )

    azure_openai_temperature: float = Field(
        default=0.7,
        description="Temperature for Azure OpenAI models"
    )

    azure_openai_max_retries: int = Field(
        default=3,
        description="Maximum retries for Azure OpenAI API calls"
    )

    azure_openai_timeout: int = Field(
        default=120,
        description="Timeout for Azure OpenAI API calls (seconds)"
    )

    # Backward compatibility (deprecated - use azure_* fields)
    openai_api_key: Optional[str] = Field(
        default=None,
        description="[DEPRECATED] Use azure_openai_key instead"
    )

    openai_model: Optional[str] = Field(
        default=None,
        description="[DEPRECATED] Use azure_openai_deployment instead"
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
    # Feature Flags
    # ========================================================================

    enable_langgraph: bool = Field(
        default=True,
        description="Enable LangGraph workflows"
    )

    enable_phase2: bool = Field(
        default=True,
        description="Enable Phase 2 (hot seat debate)"
    )

    enable_caching: bool = Field(
        default=False,
        description="Enable result caching"
    )

    cache_ttl: int = Field(
        default=3600,
        description="Cache TTL (seconds)"
    )

    enable_api_keys: bool = Field(
        default=False,
        description="Require API keys for endpoints"
    )

    api_keys: List[str] = Field(
        default=[],
        description="Valid API keys (if enabled)"
    )

    # ========================================================================
    # Agent Configuration
    # ========================================================================

    agent_registry_enabled: bool = Field(
        default=True,
        description="Use agent registry system"
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

    @field_validator('azure_openai_key')
    @classmethod
    def validate_azure_openai_key(cls, v: str) -> str:
        """Validate Azure OpenAI API key is set."""
        if not v or v == "":
            raise ValueError(
                "AZURE_OPENAI_KEY must be set. "
                "Get your key from Azure Portal > Azure OpenAI Service > Keys and Endpoint"
            )
        return v

    @field_validator('azure_openai_endpoint')
    @classmethod
    def validate_azure_endpoint(cls, v: str) -> str:
        """Validate Azure endpoint URL format."""
        if not v.startswith(('https://', 'http://')):
            raise ValueError("Azure endpoint must be a valid URL starting with https:// or http://")
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
    def azure_openai_config(self) -> dict:
        """Get Azure OpenAI configuration as dict."""
        return {
            "azure_endpoint": self.azure_openai_endpoint,
            "api_key": self.azure_openai_key,
            "api_version": self.azure_openai_api_version,
            "azure_deployment": self.azure_openai_deployment,
            "temperature": self.azure_openai_temperature,
            "max_retries": self.azure_openai_max_retries,
            "timeout": self.azure_openai_timeout
        }

    @property
    def openai_config(self) -> dict:
        """
        [DEPRECATED] Get OpenAI configuration as dict.
        Use azure_openai_config instead.

        Provided for backward compatibility.
        """
        # Map to Azure config for backward compatibility
        return {
            "api_key": self.azure_openai_key,
            "model": self.azure_openai_deployment,
            "temperature": self.azure_openai_temperature,
            "max_retries": self.azure_openai_max_retries,
            "timeout": self.azure_openai_timeout,
            # Add Azure-specific fields
            "azure_endpoint": self.azure_openai_endpoint,
            "api_version": self.azure_openai_api_version
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
                'azure_openai_key',
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
            "Azure OpenAI": [
                'azure_openai_endpoint',
                'azure_openai_deployment',
                'azure_openai_api_version',
                'azure_openai_temperature',
                'azure_openai_key'
            ],
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

    def get_env_template(self) -> str:
        """Generate .env template file content."""
        template = """# Azure OpenAI Configuration (REQUIRED)
AZURE_OPENAI_KEY=your-azure-openai-key-here
AZURE_OPENAI_ENDPOINT=https://sparkapi.spglobal.com/v1/sparkassist
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_TEMPERATURE=0.7

# API Configuration
API_TITLE=Renewable Opportunity Identifier API
API_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=false

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=true
LOG_LEVEL=info
WORKERS=1

# Job Configuration
MAX_COUNTRIES=15
MIN_COUNTRIES=2
DEFAULT_PEER_RANKERS=3
MAX_PEER_RANKERS=5
MIN_PEER_RANKERS=2
JOB_TIMEOUT_SECONDS=300

# Storage Configuration
STORAGE_BACKEND=memory
MAX_JOBS_IN_MEMORY=1000

# Redis Configuration (if using redis backend)
REDIS_URL=redis://localhost:6379/0
REDIS_KEY_PREFIX=roi:job:
REDIS_TTL=86400

# Feature Flags
ENABLE_LANGGRAPH=true
ENABLE_PHASE2=true
ENABLE_CACHING=false
PARALLEL_EXECUTION=true

# Directories
REPORTS_DIR=reports
DATA_DIR=data
LOGS_DIR=logs
TEMP_DIR=temp
"""
        return template

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
        >>> print(settings.azure_openai_config)
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
        azure_openai_key="test-key-not-used",
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
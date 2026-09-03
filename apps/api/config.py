#!/usr/bin/env python3
"""
config.py --- runtime configuration via pydantic-settings

Contains:
    Settings: typed application settings loaded from the environment
    get_settings(): cached accessor for the Settings singleton
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Loads typed application settings from the environment.

    Attributes:
        app_version: Current application version string.
        database_url: Async SQLAlchemy DSN for the audit Postgres instance.
        redis_url: Connection URL for the Redis instance.
        rate_limit_requests: Requests allowed per client per window.
        rate_limit_window_seconds: Length of the fixed rate-limit window.
        otel_exporter_otlp_endpoint: OTLP collector endpoint; tracing is off when empty.
        otel_service_name: Resource service.name reported to the collector.
    """

    # .env is shared with postgres/console/MCP, so non-API keys must not
    # fail validation -- forbidding extras here crashed the API at import.
    model_config = SettingsConfigDict(env_prefix="AGENTFLOW_", env_file=".env", extra="ignore")

    app_version: str = "0.1.0"
    database_url: str = "postgresql+asyncpg://agentflow:change-me@postgres:5432/agentflow"
    redis_url: str = "redis://redis:6379/0"
    db_pool_size: int = 20  # per-instance; see issue #109 for sizing notes
    db_max_overflow: int = 20
    db_pool_timeout: int = 30  # seconds to wait for a free connection
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    otel_exporter_otlp_endpoint: str = ""
    otel_service_name: str = "agentflow-api"


@lru_cache
def get_settings() -> Settings:
    """Returns the cached Settings singleton."""
    return Settings()

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
    """

    model_config = SettingsConfigDict(env_prefix="AGENTFLOW_", env_file=".env")

    app_version: str = "0.1.0"
    database_url: str = "postgresql+asyncpg://agentflow:change-me@postgres:5432/agentflow"
    redis_url: str = "redis://redis:6379/0"
    db_pool_size: int = 20
    db_max_overflow: int = 20
    db_pool_timeout: int = 30  # seconds to wait for a free connection


@lru_cache
def get_settings() -> Settings:
    """Returns the cached Settings singleton."""
    return Settings()

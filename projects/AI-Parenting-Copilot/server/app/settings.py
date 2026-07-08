# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 22:55:00


"""Application settings for AI Parenting Copilot.

Settings are intentionally small in APC-T002. Database, MQTT and PowerSync are
represented as configuration contracts, but no connection is opened until later tasks.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["dev", "test", "prod"]


class DatabaseSettings(BaseSettings):
    """Database configuration contract.

    `url=None` means dev/mock mode. APC-T003 wires the real async engine.
    """

    url: str | None = None
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


class MQTTSettings(BaseSettings):
    """Mosquitto configuration placeholder used by later mmWave tasks."""

    host: str = "127.0.0.1"
    port: int = 1883
    username: str | None = None
    password: str | None = None


class PowerSyncSettings(BaseSettings):
    """PowerSync service endpoint contract."""

    url: str | None = None


class ModelGatewaySettings(BaseSettings):
    """Factory Smart Proxy configuration."""

    base_url: str = "http://127.0.0.1:4000"
    default_plan: str = "parenting-local-first"
    timeout_seconds: float = 30.0


class ObservabilitySettings(BaseSettings):
    """Logging, metrics and tracing switches."""

    json_logs: bool = True
    metrics_enabled: bool = True
    tracing_enabled: bool = True
    service_name: str = "ai-parenting-copilot"
    otlp_endpoint: str | None = None


class Settings(BaseSettings):
    """Root settings loaded from `.env` and `PARENTING_*` env vars."""

    model_config = SettingsConfigDict(
        env_prefix="PARENTING_",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "AI Parenting Copilot"
    env: Environment = "dev"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    mqtt: MQTTSettings = Field(default_factory=MQTTSettings)
    powersync: PowerSyncSettings = Field(default_factory=PowerSyncSettings)
    model_gateway: ModelGatewaySettings = Field(default_factory=ModelGatewaySettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)

    @property
    def is_dev_mode(self) -> bool:
        """Return True when the app may start without external infrastructure."""

        return self.env in {"dev", "test"}

    @property
    def db_mode(self) -> str:
        """Human-readable DB mode for health responses."""

        if self.database.url:
            return "configured"
        if self.is_dev_mode:
            return "dev-mock"
        return "missing"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings for application runtime."""

    return Settings()


def reset_settings_cache() -> None:
    """Clear settings cache for tests."""

    get_settings.cache_clear()

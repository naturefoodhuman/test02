# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
#
# app/settings.py —— 应用配置（pydantic-settings 分层加载）。
# 依据：ENGINEERING_DESIGN §8.1（分层加载 SSOT 模式）、§8.2（配置文件清单）、§8.4（多环境）；
#       ARCHITECTURE_FINAL §18（配置体系）；TASK_BACKLOG APC-T002（PARENTING_ 前缀 + __ 嵌套）。
# 设计：env_prefix="PARENTING_"、env_nested_delimiter="__"，与 .env.example 对齐。
#       未配置 DB 时 dev/mock 模式可启动（APC-T002 验收标准）。

"""应用配置（pydantic-settings 分层加载）。

加载顺序（ENGINEERING_DESIGN §8.1）：
    _infra/defaults/*.yaml → config/*.yaml → runtime/*.yaml → .env → _infra/.env
    → 环境变量 PARENTING_* → CLI --overrides

本模块用 ``pydantic-settings``：``env_prefix="PARENTING_"``、``env_nested_delimiter="__"``，
与 ``.env.example`` 对齐（如 ``PARENTING_DATABASE__URL`` → ``settings.database.url``）。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根（server/app/settings.py → 上两级为项目根）。
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
RUNTIME_DIR = PROJECT_ROOT / "runtime"


class DatabaseSettings(BaseSettings):
    """PostgreSQL 连接配置（架构 §7 存储架构）。"""

    url: str = Field(
        default="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting",
        description="SQLAlchemy async URL",
    )
    echo: bool = Field(default=False, description="SQL 回显（dev 调试用）")
    pool_size: int = Field(default=5, ge=1)
    max_overflow: int = Field(default=10, ge=0)


class MqttSettings(BaseSettings):
    """Mosquitto MQTT 配置（架构 §4.2 传感器证据流）。"""

    host: str = "127.0.0.1"
    port: int = 1883
    client_id: str = "parenting-server"
    keepalive: int = 60
    # TLS / 用户名密码等在 prod 通过 _infra/.env 注入，此处仅占位默认。
    username: str | None = None
    password: str | None = None


class HttpSettings(BaseSettings):
    """HTTP 服务配置（架构 §15 API）。"""

    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://127.0.0.1:5173"])
    # 家庭局域网内 TLS（架构 §15.1）；dev 默认关闭。
    tls_enabled: bool = False


class ModelsSettings(BaseSettings):
    """模型网关配置（架构 §11.8 ModelClient 复用工厂）。

    复用工厂 smart-proxy:4000 / litellm:4001；dev 用 FakeModelClient。
    """

    gateway_base_url: str = "http://127.0.0.1:4000"
    timeout_seconds: float = Field(default=30.0, gt=0)
    # dev 模式启用 FakeModelClient，避免依赖外部模型后端（APC-T002 验收）。
    use_fake_client: bool = True


class PrivacySettings(BaseSettings):
    """脱敏/出站策略（架构 §19 隐私，复用工厂 privacy_policy.yaml）。"""

    # 出站到云 LLM 前强制脱敏；dev 可关以观察原始数据。
    redact_on_outbound: bool = True
    # 是否允许任何数据出站到云；dev 默认禁止，仅本地模型。
    allow_cloud_egress: bool = False


class NotificationSettings(BaseSettings):
    """通知通道配置（架构 §14 告警送达）。"""

    fcm_credentials_path: str | None = None
    # 本地兜底通道（架构 §23）：TTS 桌面播报 + macOS 通知。
    local_tts_enabled: bool = True
    # 升级时序（分钟），具体策略读 config/notification.yaml，此处仅默认占位。
    escalation_minutes: list[int] = Field(default_factory=lambda: [1, 3, 9])


class ObservabilitySettings(BaseSettings):
    """可观测性配置（架构 §22）。"""

    log_level: str = "INFO"
    log_format: str = "json"  # json | console
    metrics_enabled: bool = True
    metrics_path: str = "/metrics"
    tracing_enabled: bool = False
    otlp_endpoint: str | None = None


class Settings(BaseSettings):
    """应用顶层配置（聚合各域子配置）。

    环境变量映射示例：
        PARENTING_ENV=dev
        PARENTING_DATABASE__URL=postgresql+asyncpg://...
        PARENTING_MQTT__HOST=127.0.0.1
        PARENTING_HTTP__PORT=8000
        PARENTING_MODELS__USE_FAKE_CLIENT=true
    """

    model_config = SettingsConfigDict(
        env_prefix="PARENTING_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
        env_file=(".env", str(PROJECT_ROOT.parent / "_infra" / ".env")),
        env_file_encoding="utf-8",
    )

    env: str = Field(default="dev", description="dev | staging | prod")
    debug: bool = Field(default=False, description="调试模式开关")

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    mqtt: MqttSettings = Field(default_factory=MqttSettings)
    http: HttpSettings = Field(default_factory=HttpSettings)
    models: ModelsSettings = Field(default_factory=ModelsSettings)
    privacy: PrivacySettings = Field(default_factory=PrivacySettings)
    notification: NotificationSettings = Field(default_factory=NotificationSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)

    @field_validator("env")
    @classmethod
    def _validate_env(cls, v: str) -> str:
        allowed = {"dev", "staging", "prod"}
        v_lower = v.lower()
        if v_lower not in allowed:
            raise ValueError(f"env must be one of {allowed}, got {v!r}")
        return v_lower

    @property
    def is_dev(self) -> bool:
        """是否为 dev/mock 模式（APC-T002 验收：未配 DB 时可启动）。"""
        return self.env == "dev"

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取进程级单例 Settings（lru_cache 缓存）。

    测试通过 ``get_settings.cache_clear()`` 重置，或直接构造 ``Settings()``。
    """
    return Settings()


__all__ = [
    "CONFIG_DIR",
    "PROJECT_ROOT",
    "RUNTIME_DIR",
    "DatabaseSettings",
    "HttpSettings",
    "ModelsSettings",
    "MqttSettings",
    "NotificationSettings",
    "ObservabilitySettings",
    "PrivacySettings",
    "Settings",
    "get_settings",
]

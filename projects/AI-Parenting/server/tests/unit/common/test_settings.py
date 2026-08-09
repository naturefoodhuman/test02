# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
"""Settings 环境变量覆盖单元测试（APC-T002 测试要求：settings 环境变量覆盖）。"""

from __future__ import annotations

import pytest

from server.app.settings import Settings, get_settings


def test_default_settings_is_dev():
    s = Settings()
    assert s.env == "dev"
    assert s.is_dev is True
    assert s.is_prod is False


def test_env_prefix_and_nested_delimiter(monkeypatch):
    """PARENTING_ 前缀 + __ 嵌套覆盖。"""
    monkeypatch.setenv("PARENTING_ENV", "prod")
    monkeypatch.setenv("PARENTING_DATABASE__URL", "postgresql+asyncpg://u:p@h/db")
    monkeypatch.setenv("PARENTING_DATABASE__ECHO", "true")
    monkeypatch.setenv("PARENTING_MQTT__HOST", "mqtt.local")
    monkeypatch.setenv("PARENTING_MQTT__PORT", "8883")
    monkeypatch.setenv("PARENTING_HTTP__PORT", "9000")
    monkeypatch.setenv("PARENTING_MODELS__USE_FAKE_CLIENT", "false")
    get_settings.cache_clear()
    s = get_settings()
    assert s.env == "prod"
    assert s.database.url == "postgresql+asyncpg://u:p@h/db"
    assert s.database.echo is True
    assert s.mqtt.host == "mqtt.local"
    assert s.mqtt.port == 8883
    assert s.http.port == 9000
    assert s.models.use_fake_client is False
    assert s.is_prod is True


def test_invalid_env_rejected():
    with pytest.raises(ValueError, match="env must be one of"):
        Settings(env="qa")


def test_env_case_insensitive():
    s = Settings(env="PROD")
    assert s.env == "prod"


def test_cors_default():
    s = Settings()
    assert "http://127.0.0.1:5173" in s.http.cors_origins


def test_observability_defaults():
    s = Settings()
    assert s.observability.log_level == "INFO"
    assert s.observability.metrics_enabled is True

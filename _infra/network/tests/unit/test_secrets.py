# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 16:12:00 CST

"""单元测试：密钥管理"""

import os
import pytest

from _infra.network.core.secrets import (
    validate_secrets,
    get_secret,
    get_pii_encryption_key,
    SecretNotFoundError,
    has_tavily_key,
)


def test_get_secret_optional(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    assert get_secret("TAVILY_API_KEY", required=False) is None


def test_get_secret_required_missing(monkeypatch):
    monkeypatch.delenv("PII_MAP_ENCRYPTION_KEY", raising=False)
    with pytest.raises(SecretNotFoundError):
        get_secret("PII_MAP_ENCRYPTION_KEY", required=True)


def test_get_pii_key(monkeypatch):
    monkeypatch.setenv("PII_MAP_ENCRYPTION_KEY", "a" * 32)
    key = get_pii_encryption_key()
    assert len(key) >= 16


def test_validate_secrets_success(monkeypatch):
    monkeypatch.setenv("PII_MAP_ENCRYPTION_KEY", "supersecretkey123456")
    validate_secrets()  # should not raise


def test_validate_secrets_missing(monkeypatch):
    monkeypatch.delenv("PII_MAP_ENCRYPTION_KEY", raising=False)
    with pytest.raises(SecretNotFoundError):
        validate_secrets()


def test_has_tavily(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "tv-xxx")
    assert has_tavily_key() is True

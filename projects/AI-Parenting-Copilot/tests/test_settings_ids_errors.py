# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 22:55:00


"""APC-T002 unit tests for settings, IDs, clocks and error mapping."""

from __future__ import annotations

import re
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.app.common.clock import ensure_aware, to_utc, utc_now
from server.app.common.errors import AppError
from server.app.common.ids import is_ulid, new_ulid
from server.app.gateway.exception_handlers import register_exception_handlers
from server.app.settings import Settings


def test_settings_environment_nested_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PARENTING_APP_NAME", "Test Parenting")
    monkeypatch.setenv("PARENTING_DATABASE__URL", "postgresql+asyncpg://u:p@localhost/db")
    monkeypatch.setenv("PARENTING_MODEL_GATEWAY__DEFAULT_PLAN", "unit-plan")

    settings = Settings()

    assert settings.app_name == "Test Parenting"
    assert settings.database.url == "postgresql+asyncpg://u:p@localhost/db"
    assert settings.model_gateway.default_plan == "unit-plan"
    assert settings.db_mode == "configured"


def test_ulid_format_and_validation() -> None:
    value = new_ulid()

    assert re.fullmatch(r"[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{26}", value)
    assert is_ulid(value)
    assert not is_ulid("not-a-ulid")


def test_clock_requires_timezone_aware() -> None:
    now = utc_now()

    assert now.tzinfo is not None
    assert to_utc(now).tzinfo == UTC
    with pytest.raises(ValueError, match="timezone-aware"):
        ensure_aware(datetime(2026, 1, 1))


def test_app_error_mapping_contract() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    async def boom() -> None:
        raise AppError(
            "bad input",
            code="BAD_INPUT",
            status_code=418,
            evidence={"field": "x"},
        )

    response = TestClient(app, raise_server_exceptions=False).get(
        "/boom",
        headers={"x-request-id": "req-test"},
    )

    assert response.status_code == 418
    assert response.json() == {
        "code": "BAD_INPUT",
        "message": "bad input",
        "evidence": {"field": "x"},
        "trace_id": "unknown",
    }

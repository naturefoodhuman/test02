# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 18:30:00

"""Regression tests for DB integration URL rendering."""

from __future__ import annotations

from tests.integration.test_db_repository_adapters import _temp_database_urls


def test_temp_database_urls_preserve_password(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv(
        "PARENTING_DATABASE__URL",
        "postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting",
    )

    admin_url, temp_url = _temp_database_urls("apc_tmp")

    assert "***" not in admin_url
    assert "***" not in temp_url
    assert "parenting:parenting" in admin_url
    assert admin_url.endswith("/parenting")
    assert temp_url.endswith("/apc_tmp")

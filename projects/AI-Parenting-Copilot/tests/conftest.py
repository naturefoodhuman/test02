# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 19:03:00

"""Shared pytest fixtures for AI Parenting Copilot tests.

The normal unit/dev test target must remain hermetic even when a developer has
`PARENTING_DATABASE__URL` exported from a previous DB integration run. PostgreSQL
coverage lives under tests marked `integration`; all other tests should exercise
the in-memory/dev-mock repositories by default.
"""

from __future__ import annotations

import pytest

_DB_ENV_VARS = ("PARENTING_DATABASE__URL", "PARENTING_DATABASE_URL")


@pytest.fixture(autouse=True)
def isolate_non_integration_tests_from_db_env(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    """Keep non-integration tests on dev-mock storage despite shell DB env vars."""

    if request.node.get_closest_marker("integration") is not None:
        return
    for env_name in _DB_ENV_VARS:
        monkeypatch.delenv(env_name, raising=False)

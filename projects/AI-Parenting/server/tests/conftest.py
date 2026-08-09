# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
#
# tests/conftest.py —— 共享 pytest 夹具。
# 依据：TASK_BACKLOG APC-T002 测试要求；ENGINEERING_DESIGN §12（测试策略）。
# 设计：提供隔离的 Settings、Container、TestClient 夹具，避免污染进程级单例。

"""共享 pytest 夹具。

提供隔离的 ``Settings``、``Container``、``FastAPI TestClient`` 夹具，
每个测试用独立实例，避免污染进程级单例（``get_settings``/``get_container`` 的 lru_cache）。
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from server.app.di import build_container, reset_container, set_container
from server.app.main import clear_workers, create_app
from server.app.settings import get_settings


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """每个测试隔离：清空 PARENTING_* 环境变量 + 重置单例缓存。"""
    # 清掉所有 PARENTING_ 前缀变量，避免测试间串扰。
    for key in list(os.environ):
        if key.startswith("PARENTING_"):
            monkeypatch.delenv(key, raising=False)
    get_settings.cache_clear()
    reset_container()
    clear_workers()
    yield
    get_settings.cache_clear()
    reset_container()
    clear_workers()


@pytest.fixture
def settings():
    """默认 dev Settings（无环境变量覆盖）。"""
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
def container(settings):
    """独立 Container（dev/mock 模式）。"""
    c = build_container(settings)
    set_container(c)
    return c


@pytest.fixture
def client(settings) -> Iterator[TestClient]:
    """FastAPI TestClient（无业务 worker）。"""
    clear_workers()
    app = create_app(settings)
    with TestClient(app) as c:
        yield c

# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
"""HTTP 集成测试（需安装 fastapi + httpx）。

若环境未安装 fastapi，则自动跳过，不让整套测试失败。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

fastapi = pytest.importorskip("fastapi", reason="未安装 fastapi，跳过 HTTP 集成测试")
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health_endpoint() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_greet_endpoint() -> None:
    r = client.get("/greet", params={"name": "李四"})
    assert r.status_code == 200
    assert "李四" in r.json()["message"]

# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
"""core 纯逻辑单测（无需 fastapi，任何环境可跑）。"""
from __future__ import annotations

import sys
from pathlib import Path

# 让测试无需安装即可找到 src/app
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from app.core import build_greeting, health_payload  # noqa: E402


def test_build_greeting_with_name() -> None:
    assert build_greeting("张三") == "你好，张三！欢迎使用 FORGE Factory。"


def test_build_greeting_empty_uses_default() -> None:
    assert "朋友" in build_greeting("")
    assert "朋友" in build_greeting(None)
    assert "朋友" in build_greeting("   ")


def test_health_payload() -> None:
    p = health_payload("1.2.3")
    assert p == {"status": "ok", "version": "1.2.3"}

# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
"""时钟单元测试（APC-T002 测试要求：时间 timezone-aware）。"""

from __future__ import annotations

from datetime import UTC, datetime

from server.app.common.clock import SystemClock, ensure_aware, now_utc


def test_now_utc_is_timezone_aware_utc():
    t = now_utc()
    assert t.tzinfo is not None
    assert t.utcoffset() == UTC.utcoffset(None)


def test_system_clock_returns_utc():
    t = SystemClock().now()
    assert t.tzinfo is not None


def test_ensure_aware_attaches_utc_to_naive():
    naive = datetime(2026, 8, 7, 12, 0, 0)
    aware = ensure_aware(naive)
    assert aware.tzinfo is not None
    assert aware.utcoffset() == UTC.utcoffset(None)
    # 原始值不变（除 tzinfo）
    assert aware.year == 2026 and aware.hour == 12


def test_ensure_aware_preserves_already_aware():
    aware = datetime(2026, 8, 7, 12, 0, 0, tzinfo=UTC)
    out = ensure_aware(aware)
    assert out is aware

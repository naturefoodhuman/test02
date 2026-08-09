# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
"""DI 容器单元测试。"""

from __future__ import annotations

from server.app.common.clock import Clock
from server.app.common.event_bus import EventBus
from server.app.di import build_container
from server.app.settings import Settings


def test_build_container_assembles_basics():
    c = build_container(Settings())
    assert c.settings.env == "dev"
    assert isinstance(c.clock, Clock)
    assert isinstance(c.event_bus, EventBus)


def test_container_override_and_get():
    c = build_container(Settings())
    sentinel = object()
    c.override("fake_model", sentinel)
    assert c.get("fake_model") is sentinel
    assert c.get("missing") is None

# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
"""事件总线单元测试。"""

from __future__ import annotations

from server.app.common.event_bus import EventBus, InMemoryEventBus


async def test_in_memory_bus_delivers_to_subscribers():
    bus = InMemoryEventBus()
    received: list[dict] = []

    async def handler(payload):
        received.append(payload)

    await bus.subscribe("events.changed", handler)
    await bus.publish("events.changed", {"event_id": "01KZ", "type": "feed"})
    assert received == [{"event_id": "01KZ", "type": "feed"}]


async def test_in_memory_bus_isolates_channels():
    bus = InMemoryEventBus()
    a: list[dict] = []
    b: list[dict] = []

    async def ha(p):
        a.append(p)

    async def hb(p):
        b.append(p)

    await bus.subscribe("a", ha)
    await bus.subscribe("b", hb)
    await bus.publish("a", {"x": 1})
    assert a == [{"x": 1}]
    assert b == []


async def test_in_memory_bus_serializes_through_json():
    """payload 经 JSON 序列化/反序列化，模拟 PG NOTIFY 边界。"""
    bus = InMemoryEventBus()
    got: list[dict] = []

    async def handler(p):
        got.append(p)

    await bus.subscribe("ch", handler)
    # datetime 不可 JSON 序列化，应被 default=str 转字符串而非崩溃
    await bus.publish("ch", {"ts": "2026-08-07T12:00:00+00:00"})
    assert got[0]["ts"] == "2026-08-07T12:00:00+00:00"


async def test_in_memory_bus_start_stop():
    bus = InMemoryEventBus()
    await bus.start()
    await bus.stop()


def test_in_memory_bus_satisfies_protocol():
    assert isinstance(InMemoryEventBus(), EventBus)

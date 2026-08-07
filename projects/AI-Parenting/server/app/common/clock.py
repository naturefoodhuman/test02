# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
#
# common/clock.py —— 统一时钟（timezone-aware）。
# 依据：TASK_BACKLOG APC-T002（时间统一 timezone-aware）；ENGINEERING_DESIGN §5。
# 设计：所有时间一律 timezone-aware（UTC），杜绝 naive datetime 渗入领域层。
# 测试可通过注入 Clock 替身（freezegun 或 fake）控制时间，不依赖系统时钟。

"""统一时钟抽象。

架构铁律：所有时间一律 timezone-aware（UTC），禁止 naive datetime 渗入领域层。
测试通过注入 ``Clock`` 替身控制时间，不依赖系统时钟（依赖注入原则）。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol


class Clock(Protocol):
    """时钟协议：返回当前 timezone-aware datetime（UTC）。"""

    def now(self) -> datetime: ...


class SystemClock:
    """系统时钟实现，返回 UTC aware datetime。"""

    def now(self) -> datetime:
        return datetime.now(tz=timezone.utc)


# 默认时钟单例（进程级）。测试应通过 DI 注入替身，不直接改此全局。
_default_clock: Clock = SystemClock()


def get_clock() -> Clock:
    """获取进程默认时钟。"""
    return _default_clock


def set_default_clock(clock: Clock) -> None:
    """替换进程默认时钟（仅测试用；生产代码不应调用）。"""
    global _default_clock
    _default_clock = clock


def now_utc() -> datetime:
    """便捷函数：当前 UTC aware datetime。"""
    return _default_clock.now()


def ensure_aware(dt: datetime) -> datetime:
    """确保 datetime 为 timezone-aware；naive 视为 UTC 并附加 tzinfo。

    防御性辅助：外部输入（如 DB 反序列化偶发）可能为 naive，统一在此归一。
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


__all__ = [
    "Clock",
    "SystemClock",
    "get_clock",
    "set_default_clock",
    "now_utc",
    "ensure_aware",
]

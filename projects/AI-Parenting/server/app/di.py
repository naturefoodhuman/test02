# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
#
# app/di.py —— 依赖装配（Dependency Injection）。
# 依据：ENGINEERING_DESIGN §5（核心抽象与接口设计，Protocol + DI）；
#       ARCHITECTURE_FINAL §3（模块划分与职责边界）；TASK_BACKLOG APC-T002。
# 设计：进程级单例容器 + FastAPI Depends 请求作用域工厂。
#       T002 只装配基础依赖（Settings/Clock/EventBus），业务模块在各自任务接入。
#       测试可替换容器内任意组件（注入替身）。

"""依赖装配（Dependency Injection）。

架构（ENGINEERING_DESIGN §5）：所有抽象以 ``Protocol`` + DI 实现，测试可注入替身。
本模块提供进程级单例容器（``Container``）与 FastAPI ``Depends`` 工厂。

APC-T002 只装配基础依赖（Settings / Clock / EventBus），业务模块
（Repository / Orchestrator / RuleModule / NotificationChannel 等）在各自任务接入，
通过 ``Container`` 扩展，不改内核（开闭原则）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from fastapi import Request

from .common.clock import Clock, SystemClock
from .common.event_bus import EventBus, InMemoryEventBus
from .settings import Settings, get_settings

if TYPE_CHECKING:
    pass


@dataclass
class Container:
    """进程级依赖容器（单例）。

    持有跨请求共享的无状态/可复用组件。请求作用域依赖（如 Repository）
    通过 FastAPI ``Depends`` 工厂按请求构造，不放入本容器。
    """

    settings: Settings
    clock: Clock
    event_bus: EventBus
    # 预留：model_client / rule_modules / notification_channels 等，后续任务填充。
    _extras: dict[str, object] = field(default_factory=dict)

    def override(self, key: str, value: object) -> None:
        """测试用：替换容器内组件（如注入 FakeModelClient）。"""
        self._extras[key] = value

    def get(self, key: str, default: object | None = None) -> object | None:
        return self._extras.get(key, default)


# ---- 进程级单例容器 ----
# 延迟初始化：首次访问时按 Settings 构造。测试通过 reset_container() 重置。
_container: Container | None = None


def build_container(settings: Settings | None = None) -> Container:
    """按 Settings 构造默认容器。

    dev/mock 模式：EventBus 用 InMemoryEventBus（不接真实 PG，APC-T002 验收）。
    prod 模式：后续任务替换为 PgListenEventBus（APC-T003+）。
    """
    s = settings or get_settings()
    clock: Clock = SystemClock()
    # dev 模式默认进程内事件总线；prod 在 APC-T003+ 替换为 PG LISTEN/NOTIFY。
    event_bus: EventBus = InMemoryEventBus()
    return Container(settings=s, clock=clock, event_bus=event_bus)


def get_container() -> Container:
    """获取进程级单例容器（惰性初始化）。"""
    global _container
    if _container is None:
        _container = build_container()
    return _container


def set_container(container: Container) -> None:
    """替换进程级容器（测试用，注入替身容器）。"""
    global _container
    _container = container


def reset_container() -> None:
    """重置进程级容器为 None（测试用，强制下次重建）。"""
    global _container
    _container = None


# ---- FastAPI Depends 工厂（请求作用域） ----
# 路由通过 Depends(get_settings_dep) 等注入；测试可覆盖 dependency_overrides。


def _container_from_request(request: Request) -> Container:
    """从 app.state 取容器（lifespan 中挂载，运行时存在）。"""
    return request.app.state.container  # type: ignore[no-any-return]


def get_settings_dep(request: Request) -> Settings:
    """FastAPI 依赖：从 app.state 取 Settings（与容器同源）。"""
    return _container_from_request(request).settings


def get_clock_dep(request: Request) -> Clock:
    """FastAPI 依赖：从 app.state 取 Clock。"""
    return _container_from_request(request).clock


def get_event_bus_dep(request: Request) -> EventBus:
    """FastAPI 依赖：从 app.state 取 EventBus。"""
    return _container_from_request(request).event_bus


__all__ = [
    "Container",
    "build_container",
    "get_clock_dep",
    "get_container",
    "get_event_bus_dep",
    "get_settings_dep",
    "reset_container",
    "set_container",
]

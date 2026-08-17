# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
#
# app/di.py —— 依赖装配（Dependency Injection）。
# 依据：ENGINEERING_DESIGN §5（核心抽象与接口设计，Protocol + DI）；
#       ARCHITECTURE_FINAL §3（模块划分与职责边界）；TASK_BACKLOG APC-T002。
# 设计：进程级单例容器 + FastAPI Depends 请求作用域工厂。
#       T002 装配基础依赖（Settings/Clock/EventBus）；T007 装配 Auth 无状态单例
#       （JwtService/PasswordHasher）；业务请求作用域依赖（Repository/AuthService）
#       由 FastAPI Depends 按请求构造，不放入本容器。测试可替换容器内任意组件（注入替身）。

"""依赖装配（Dependency Injection）。

架构（ENGINEERING_DESIGN §5）：所有抽象以 ``Protocol`` + DI 实现，测试可注入替身。
本模块提供进程级单例容器（``Container``）与 FastAPI ``Depends`` 工厂。

APC-T002 装配基础依赖（Settings / Clock / EventBus）；APC-T007 装配 Auth 无状态单例
（``JwtService`` / ``PasswordHasher``）。请求作用域依赖（``UserRepository`` / ``AuthService``）
由 FastAPI ``Depends`` 按请求构造，不放入本容器（架构 §5.2：Repository 请求作用域）。
业务模块（Orchestrator / RuleModule / NotificationChannel 等）在各自任务接入，
通过 ``Container`` 扩展，不改内核（开闭原则）。
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, Request

from .auth.domain import JwtService, PasswordHasher, Principal
from .auth.service.auth_service import AuthService
from .auth.service.jwt import Hs256JwtService
from .auth.service.password import Pbkdf2PasswordHasher
from .common.clock import Clock, SystemClock
from .common.errors import AuthError
from .common.event_bus import EventBus, InMemoryEventBus
from .model_gateway.client import FakeModelClient, SmartProxyModelClient
from .model_gateway.domain import ModelClient
from .model_gateway.routing import load_plans
from .rule_engine.registry import RuleRegistry
from .settings import CONFIG_DIR, Settings, get_settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from .events.service.idempotency import EventService
    from .observability.audit import AuditService
    from .rule_engine.evidence_repo import EvidencePolicyRepository


@dataclass
class Container:
    """进程级依赖容器（单例）。

    持有跨请求共享的无状态/可复用组件。请求作用域依赖（如 Repository）
    通过 FastAPI ``Depends`` 工厂按请求构造，不放入本容器。
    """

    settings: Settings
    clock: Clock
    event_bus: EventBus
    # Auth 无状态单例（APC-T007）：JwtService / PasswordHasher，跨请求复用。
    # 请求作用域的 UserRepository / AuthService 由 FastAPI Depends 按请求构造，不放入本容器。
    jwt_service: JwtService
    password_hasher: PasswordHasher
    # RuleRegistry 进程级单例（APC-T018）：启动期注册 RuleModule（T020+ 接入），运行期只读。
    rule_registry: RuleRegistry
    # ModelClient 进程级单例（APC-T024）：项目内唯一 LLM/VLM 入口（架构 §11.8）。
    # dev 用 FakeModelClient（不联网）；prod 用 SmartProxyModelClient（工厂 Smart Proxy 4000）。
    model_client: ModelClient
    # 预留：notification_channels 等，后续任务填充。
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
    # Auth 无状态单例（APC-T007）：HS256 JWT + PBKDF2 密码哈希。
    # JwtService 过期校验用同一 clock（与 AuthService.issue_token 对称）。
    jwt_service: JwtService = Hs256JwtService(
        secret=s.auth.jwt_secret, access_ttl_seconds=s.auth.access_ttl_seconds, clock=clock
    )
    password_hasher: PasswordHasher = Pbkdf2PasswordHasher(iterations=s.auth.password_iterations)
    # RuleRegistry 进程级单例（APC-T018）：启动期注册 RuleModule（T020+ 接入），运行期只读。
    rule_registry = RuleRegistry()
    # ModelClient 进程级单例（APC-T024）：项目内唯一 LLM/VLM 入口。
    # dev 用 FakeModelClient（不联网，CI 安全）；prod 用 SmartProxyModelClient（工厂 4000）。
    model_client = _build_model_client(s)
    return Container(
        settings=s,
        clock=clock,
        event_bus=event_bus,
        jwt_service=jwt_service,
        password_hasher=password_hasher,
        rule_registry=rule_registry,
        model_client=model_client,
    )


def _build_model_client(s: Settings) -> ModelClient:
    """按 Settings.models 选 ModelClient（APC-T024）。

    ``use_fake_client=True``（dev 默认）→ FakeModelClient（不联网）；
    否则 → SmartProxyModelClient（加载 config/routing_plans.yaml，POST 工厂 4000）。
    """
    if s.models.use_fake_client:
        return FakeModelClient()
    plans = load_plans(CONFIG_DIR / "routing_plans.yaml")
    return SmartProxyModelClient(base_url=s.models.gateway_base_url, plans=plans)


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
    return request.app.state.container


def get_settings_dep(request: Request) -> Settings:
    """FastAPI 依赖：从 app.state 取 Settings（与容器同源）。"""
    return _container_from_request(request).settings


def get_clock_dep(request: Request) -> Clock:
    """FastAPI 依赖：从 app.state 取 Clock。"""
    return _container_from_request(request).clock


def get_event_bus_dep(request: Request) -> EventBus:
    """FastAPI 依赖：从 app.state 取 EventBus。"""
    return _container_from_request(request).event_bus


def get_rule_registry_dep(request: Request) -> RuleRegistry:
    """FastAPI 依赖：从 app.state 取进程级 RuleRegistry 单例（APC-T018）。

    启动期注册 RuleModule（T020+），运行期只读。orchestrator/copilots 经此调用
    ``registry.evaluate(domain, input, ctx)``（架构 §5.3 单一入口）。
    """
    return _container_from_request(request).rule_registry


# ---- Auth 依赖工厂（APC-T008：请求作用域 AuthService + 鉴权 Principal）----


async def get_session_dep(request: Request) -> AsyncIterator[AsyncSession]:
    """FastAPI 依赖：按请求提供 async session（自动关闭）。

    从 container.settings 取 DB 配置，复用进程级 session factory（架构 §5.2 请求作用域）。
    """
    from .db import get_session_factory  # 延迟导入避免循环依赖

    container = _container_from_request(request)
    factory = get_session_factory(container.settings)
    async with factory() as session:
        yield session


async def get_auth_service_dep(request: Request) -> AsyncGenerator[AuthService, None]:
    """FastAPI 依赖：按请求构造 AuthService（注入 session + 无状态单例）。

    ``UserRepository`` / ``DeviceRepository`` / ``AuthService`` 均请求作用域
    （持有请求级 session）；``PasswordHasher`` / ``JwtService`` 从 container 取无状态单例（APC-T007）。
    ``session`` 传入 AuthService 以便 mutating 方法 commit（事务边界在 service，架构 §5.2）。
    """
    from .auth.infra.repository import SqlAlchemyDeviceRepository, SqlAlchemyUserRepository
    from .db import get_session_factory

    container = _container_from_request(request)
    factory = get_session_factory(container.settings)
    async with factory() as session:
        yield AuthService(
            repository=SqlAlchemyUserRepository(session),
            password_hasher=container.password_hasher,
            jwt_service=container.jwt_service,
            clock=container.clock,
            access_ttl_seconds=container.settings.auth.access_ttl_seconds,
            device_repository=SqlAlchemyDeviceRepository(session),
            session=session,
        )


def get_principal_dep(
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service_dep)],
) -> Principal:
    """FastAPI 依赖：从 Authorization: Bearer <token> 解析 Principal。

    缺失/非法 token → ``AuthError``（401，由全局异常处理器映射）。
    用法（受保护端点）::

        @router.get("/me")
        async def me(principal: Annotated[Principal, Depends(get_principal_dep)]):
            ...
    """
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise AuthError("Missing or malformed Authorization header")
    token = header[len("Bearer ") :].strip()
    if not token:
        raise AuthError("Empty bearer token")
    return auth_service.authenticate_token(token)


# ---- Events 依赖工厂（APC-T010：请求作用域 EventService + AuditService 共享 session）----


@dataclass
class EventContext:
    """Events 请求作用域上下文（EventService + AuditService 共享同一 session）。

    ``EventService`` 与 ``AuditService`` 共享请求级 ``AsyncSession``，确保 mutating 操作
    与审计写入在同一事务内提交（§10.4 不可绕过；避免 T008 阶段 audit 与业务跨 session
    的不一致窗口）。路由通过 ``EventContextDep`` 单次注入解构使用。
    """

    event_service: EventService
    audit_service: AuditService


async def get_event_context_dep(request: Request) -> AsyncGenerator[EventContext, None]:
    """FastAPI 依赖：按请求构造 EventContext（EventService + AuditService 共享 session）。

    ``SqlAlchemyObservationEventRepository`` / ``EventService`` / ``AuditService`` 均请求作用域
    （持有同一请求级 session）；``Clock`` 从 container 取进程级单例。
    ``session`` 传入 EventService 以便 mutating 方法 commit（事务边界在 service，架构 §5.2）；
    AuditService 共享同一 session，审计与业务在同一事务提交（§10.4）。
    """
    from .db import get_session_factory
    from .events.infra.repository import SqlAlchemyObservationEventRepository
    from .events.service.idempotency import EventService
    from .observability.audit import AuditService

    container = _container_from_request(request)
    factory = get_session_factory(container.settings)
    async with factory() as session:
        yield EventContext(
            event_service=EventService(
                repository=SqlAlchemyObservationEventRepository(session),
                clock=container.clock,
                session=session,
            ),
            audit_service=AuditService(session, container.clock),
        )


# ---- Rule Engine 依赖工厂（APC-T018：请求作用域 EvidencePolicyRepository）----


async def get_evidence_policy_repo_dep(
    request: Request,
) -> AsyncGenerator[EvidencePolicyRepository, None]:
    """FastAPI 依赖：按请求构造 SqlAlchemyEvidencePolicyRepository（APC-T018）。

    请求作用域（持有请求级 ``AsyncSession``）；``Clock`` 从 container 取进程级单例。
    供规则求值时取当前生效版本。事务边界在调用方（service 层 commit，架构 §5.2）。
    """
    from .db import get_session_factory
    from .rule_engine.evidence_repo import SqlAlchemyEvidencePolicyRepository

    container = _container_from_request(request)
    factory = get_session_factory(container.settings)
    async with factory() as session:
        yield SqlAlchemyEvidencePolicyRepository(session, clock=container.clock)


# ---- Rules Admin API 依赖工厂（APC-T019：RulesContext 共享 session）----


@dataclass
class RulesContext:
    """Rules 请求作用域上下文（EvidencePolicyRepository + AuditService 共享同一 session）。

    与 ``EventContext`` 同精神（§10.4）：mutating 操作（上传/激活）的审计写入与规则
    版本写入在同一事务提交，避免跨 session 不一致窗口。``EvidencePolicyRepository``
    与 ``AuditService`` 均 flush 不 commit；事务提交在 ``get_rules_context_dep``
    yield 后统一 ``commit``（请求结束，架构 §5.2 事务边界）。
    """

    evidence_repo: EvidencePolicyRepository
    audit_service: AuditService


async def get_rules_context_dep(request: Request) -> AsyncGenerator[RulesContext, None]:
    """FastAPI 依赖：按请求构造 RulesContext（EvidencePolicyRepository + AuditService 共享 session）。

    两者共享请求级 ``AsyncSession``；``Clock`` 从 container 取进程级单例。
    ``evidence_repo`` / ``audit_service`` 均 flush 不 commit；yield 后统一 ``commit``
    （mutating 操作的规则写入与审计同事务提交，§10.4 不可绕过）。只读操作（list/validate）
    commit 无副作用。
    """
    from .db import get_session_factory
    from .observability.audit import AuditService
    from .rule_engine.evidence_repo import SqlAlchemyEvidencePolicyRepository

    container = _container_from_request(request)
    factory = get_session_factory(container.settings)
    async with factory() as session:
        yield RulesContext(
            evidence_repo=SqlAlchemyEvidencePolicyRepository(session, clock=container.clock),
            audit_service=AuditService(session, container.clock),
        )
        await session.commit()


__all__ = [
    "Container",
    "EventContext",
    "RulesContext",
    "build_container",
    "get_auth_service_dep",
    "get_clock_dep",
    "get_container",
    "get_event_bus_dep",
    "get_event_context_dep",
    "get_evidence_policy_repo_dep",
    "get_principal_dep",
    "get_rule_registry_dep",
    "get_rules_context_dep",
    "get_session_dep",
    "get_settings_dep",
    "reset_container",
    "set_container",
]

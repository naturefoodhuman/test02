# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/common/audit_decorator.py —— @audit 装饰器（mutating API 强制留痕）。
# 依据：ENGINEERING_DESIGN §10.4（Audit）、§14.5（审计不可少）；ARCHITECTURE_FINAL §1.2、§22.2；
#       TASK_BACKLOG APC-T006。
# 设计：@audit(action=..., resource=...) 装饰 mutating API/service 方法；
#       调用前捕获 before 快照（由被装饰函数返回 before/after，或通过 load_before 钩子），
#       调用后写 audit_log（AuditService.append）。
#       审计写入失败 → 抛 UpstreamUnavailable（503），mutating 操作不得静默成功（§10.4）。
# 边界：装饰器不感知 HTTP；before/after 由被装饰函数提供（领域语义，装饰器不猜结构）。

"""``@audit`` 装饰器（mutating API 强制留痕，§10.4 / §14.5）。

架构（§1.2：审计不可绕过）：任何 mutating 操作用 ``@audit`` 留痕。
装饰器在 mutating 操作成功后写 audit_log；审计写入失败 → 抛 ``UpstreamUnavailable``，
mutating 操作不得静默成功（§10.4）。

被装饰函数约定（两种模式）：

1. **返回值即 after 快照**（简单场景）::

       @audit(action="create", resource="observation_event")
       async def create_event(..., audit: AuditService) -> dict:
           ...
           return after_snapshot  # dict，写入 audit_log.after

   before 通过 ``load_before`` 钩子提供（操作前加载旧状态）。

2. **返回 AuditResult（显式 before/after）**（复杂场景，如规则变更前后）::

       @audit(action="update", resource="rule")
       async def update_rule(...) -> AuditResult:
           return AuditResult(before=old, after=new, rule_version=ver)

装饰器从被装饰函数签名取 ``audit: AuditService`` 参数（FastAPI Depends 注入），
无需额外装配。``actor`` 从 logger contextvars 取（user_id/device_id/system）。
"""

from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from ..observability.audit import AuditService
from ..observability.logger import get_context


@dataclass(frozen=True)
class AuditResult:
    """被装饰函数显式返回的审计快照（复杂场景：before/after/rule_version/llm_call_id）。

    简单场景可直接返回 dict（作为 after），before 与 rule_version 通过装饰器参数或
    load_before 钩子提供。
    """

    after: dict[str, Any] | None = None
    before: dict[str, Any] | None = None
    rule_version: str | None = None
    llm_call_id: str | None = None


def audit(
    *,
    action: str,
    resource: str,
    load_before: Callable[..., Awaitable[dict[str, Any] | None]] | None = None,
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """``@audit`` 装饰器工厂。

    :param action: 审计动作（create/update/delete/confirm/export/intercept/llm_call 等）。
    :param resource: 资源描述模板，支持 ``{kwarg}`` 占位（如 ``"rule/{rule_id}"``），
                     运行时用被装饰函数关键字参数填充。
    :param load_before: 可选的异步钩子，签名与被装饰函数一致，返回 before 快照。
                        复杂场景（规则变更前后）用；简单 create 场景可省略。
    """

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 从 kwargs 取 AuditService（FastAPI Depends 注入，参数名约定为 audit）。
            audit_svc: AuditService | None = kwargs.get("audit")
            if audit_svc is None:
                # 位置参数回退：按 AuditService 类型匹配。
                for a in args:
                    if isinstance(a, AuditService):
                        audit_svc = a
                        break
            if audit_svc is None:
                raise TypeError(
                    f"@audit({action}) 被装饰函数 {func.__qualname__} 缺少 audit: AuditService 参数"
                )

            # before 快照（load_before 钩子）。
            before: dict[str, Any] | None = None
            if load_before is not None:
                before = await load_before(*args, **kwargs)

            # 执行 mutating 操作。
            result = await func(*args, **kwargs)

            # 解析 after / rule_version / llm_call_id。
            after: dict[str, Any] | None = None
            rule_version: str | None = None
            llm_call_id: str | None = None
            if isinstance(result, AuditResult):
                after = result.after
                if result.before is not None:
                    before = result.before
                rule_version = result.rule_version
                llm_call_id = result.llm_call_id
            elif isinstance(result, dict):
                after = result
            # result 为其他类型（如 None / model）时不写 after，仅记 actor/action/resource。

            # actor 从 logger contextvars 取（user_id/device_id/system），无则 system。
            ctx = get_context()
            actor = ctx.get("user_id") or ctx.get("device_id") or "system"

            # 资源描述模板填充（如 "rule/{rule_id}" → "rule/01J..."）。
            try:
                resolved_resource = resource.format(**kwargs)
            except (KeyError, IndexError):
                resolved_resource = resource

            # 写 audit_log；失败抛 UpstreamUnavailable，mutating 操作不得静默成功。
            await audit_svc.append(
                actor=actor,
                action=action,
                resource=resolved_resource,
                before=before,
                after=after,
                rule_version=rule_version,
                llm_call_id=llm_call_id,
            )
            return result

        return wrapper

    return decorator


__all__ = ["AuditResult", "audit"]

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 00:30:00


"""`@audit` decorator for mutating operations."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar, cast

from server.app.observability.audit import AuditActor, AuditRecord, AuditSink, AuditWriteError

P = ParamSpec("P")
R = TypeVar("R")
ValueProvider = Callable[..., Any]


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def _resolve_provider(
    provider: ValueProvider | None,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    if provider is None:
        return None
    return provider(*args, **kwargs)


def _find_audit_sink(args: tuple[Any, ...], kwargs: dict[str, Any]) -> AuditSink | None:
    explicit = kwargs.get("audit_sink") or kwargs.get("audit_service")
    if explicit is not None:
        return cast(AuditSink, explicit)
    for arg in args:
        candidate = getattr(arg, "audit_sink", None) or getattr(arg, "audit_service", None)
        if candidate is not None:
            return cast(AuditSink, candidate)
    return None


def audit(
    *,
    action: str,
    resource: str,
    actor: ValueProvider | None = None,
    before: ValueProvider | None = None,
    after: ValueProvider | None = None,
    high_risk: bool = True,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorate an async mutating use case with mandatory audit logging.

    If no AuditSink is available and `high_risk=True`, the operation is blocked
    after the wrapped function returns. Production mutating endpoints should inject
    AuditService through DI; tests can inject MemoryAuditSink.
    """

    def decorator(fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            call_args = tuple(args)
            call_kwargs = dict(kwargs)
            before_value = await _maybe_await(_resolve_provider(before, call_args, call_kwargs))
            result = await fn(*args, **kwargs)
            after_value = await _maybe_await(
                _resolve_provider(after, call_args, {**call_kwargs, "result": result})
            )
            if after is None and isinstance(result, dict):
                after_value = result
            actor_value = await _maybe_await(_resolve_provider(actor, call_args, call_kwargs))
            if isinstance(actor_value, AuditActor):
                audit_actor = actor_value
            elif isinstance(actor_value, dict):
                audit_actor = AuditActor(**actor_value)
            else:
                audit_actor = AuditActor(actor_kind="system")

            sink = _find_audit_sink(call_args, call_kwargs)
            if sink is None:
                if high_risk:
                    raise AuditWriteError(
                        "Audit sink is required for mutating operation",
                        evidence={"action": action, "resource": resource},
                    )
                return result

            await sink.record(
                AuditRecord(
                    actor=audit_actor,
                    action=action,
                    resource=resource,
                    before=before_value,
                    after=after_value,
                    trace_id=str(call_kwargs.get("trace_id"))
                    if call_kwargs.get("trace_id") is not None
                    else None,
                )
            )
            return result

        return wrapper

    return decorator

# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/observability/audit.py —— 不可删除审计写入服务（AuditService）。
# 依据：ENGINEERING_DESIGN §10.4（Audit，不可删除）、§6.1（audit_log 表）、§14.5（审计不可少）；
#       ARCHITECTURE_FINAL §1.2（审计不可绕过）、§22.2（审计记录内容）；TASK_BACKLOG APC-T006。
# 设计：AuditService.append() 向 audit_log 追加一条记录（append-only）。
#       审计字段：actor/action/resource/before/after/rule_version/llm_call_id；
#       trace_id/request_id 嵌入 after JSONB（架构 §6.1 表无 trace_id 列，SSOT 不改）。
#       审计写入失败 → 抛 UpstreamUnavailable（503），mutating 高风险操作不得静默成功（§10.4）。
# 边界：不提供 update/delete 方法（append-only，迁移层 REVOKE UPDATE/DELETE 强制）；
#       本服务只写不读，查询走 parenting-cli audit trail（§10.6 排查流程）。

"""不可删除审计写入服务（AuditService）。

架构（ENGINEERING_DESIGN §10.4 / §22.2）：``audit_log`` 表 append-only，
迁移层 ``REVOKE UPDATE, DELETE`` 强制不可删除。本服务只提供 ``append`` 写入，
不提供 update/delete（架构 §1.2：审计不可绕过、不可删除）。

审计字段（§6.1 表 + APC-T006 实现要求）：
    ``actor`` —— 操作者（user_id / device_id / system，String(128)）。
    ``action`` —— 动作（create/update/delete/confirm/export/intercept/llm_call 等，String(64)）。
    ``resource`` —— 被操作资源（如 ``observation_event/<id>``、``rule/<id>@<version>``，String(255)）。
    ``before`` / ``after`` —— 变更前/后快照（JSONB，可选）。
    ``rule_version`` —— 规则版本（剂量拦截/规则变更时填，String(64)）。
    ``llm_call_id`` —— 云 LLM 调用 ID（llm_call 动作时填，String(64)）。
    ``trace_id`` / ``request_id`` —— 嵌入 ``after`` JSONB（架构 §6.1 表无此列，SSOT 不改）。

写入失败（DB 异常）→ 抛 ``UpstreamUnavailable``（503），调用方的 mutating 操作不得静默成功。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.clock import Clock
from ..common.errors import UpstreamUnavailable
from ..common.ids import new_id
from ..models.rules import AuditLog
from .logger import get_context


class AuditService:
    """不可删除审计写入服务（append-only）。

    生命周期：请求作用域（FastAPI ``Depends`` 注入 session）；事务边界在 service 层。
    不持有状态，仅依赖注入的 ``AsyncSession`` 与 ``Clock``。
    """

    def __init__(self, session: AsyncSession, clock: Clock) -> None:
        self._session = session
        self._clock = clock

    async def append(
        self,
        *,
        actor: str,
        action: str,
        resource: str,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        rule_version: str | None = None,
        llm_call_id: str | None = None,
    ) -> str:
        """向 audit_log 追加一条审计记录，返回审计记录 id（ULID）。

        trace_id/request_id 从 logger contextvars 取（贯穿请求链路），嵌入 after JSONB。
        写入失败 → 抛 ``UpstreamUnavailable``（§10.4：不得静默成功）。
        """
        ctx = get_context()
        trace_id = ctx.get("trace_id")
        request_id = ctx.get("request_id")

        # trace_id/request_id 嵌入 after（架构 §6.1 表无 trace_id 列，SSOT 不改）。
        after_payload: dict[str, Any] = dict(after) if after else {}
        if trace_id is not None:
            after_payload.setdefault("_trace_id", trace_id)
        if request_id is not None:
            after_payload.setdefault("_request_id", request_id)

        audit_id = new_id()
        try:
            await self._session.execute(
                insert(AuditLog).values(
                    id=audit_id,
                    ts=self._clock.now(),
                    actor=actor,
                    action=action,
                    resource=resource,
                    before=before,
                    after=after_payload or None,
                    rule_version=rule_version,
                    llm_call_id=llm_call_id,
                )
            )
        except Exception as exc:  # DB 异常统一映射为审计失败
            raise UpstreamUnavailable(
                f"audit_log append failed: {exc.__class__.__name__}",
                evidence={"actor": actor, "action": action, "resource": resource},
            ) from exc
        return audit_id


__all__ = ["AuditService"]

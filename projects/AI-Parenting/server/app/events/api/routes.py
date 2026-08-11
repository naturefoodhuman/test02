# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/events/api/routes.py —— Events API 路由（创建/查询/纠错/软删除）。
# 依据：ENGINEERING_DESIGN §5.1（ObservationEvent 契约）、§9.1（异常）、§10.4（Audit 不可绕过）；
#       ARCHITECTURE_FINAL §5.1（事件生命周期）、§9.2（错误信封）、§15.2（Events 域 POST /api/v1/events）、§19（权限）；
#       TASK_BACKLOG APC-T010（写接口 event_id 幂等；编辑不覆盖历史走 correction；删除只置 is_deleted；
#       所有 mutating 接 @audit；同一 family/baby 可查询时间线；软删除事件不出现在普通查询但审计可追溯）。
# 设计：API 前缀 /api/v1/events；路由只做 HTTP 适配（请求/响应模型 + 调用 service + RBAC + audit）。
#       幂等：POST /events 以 event_id 幂等（service 层 upsert 去重，架构 §505）。
#       纠错：POST /events/{id}/correct 创建 correction 关系（软删除旧 + 新事件 correction_of 指向旧）。
#       软删除：DELETE /events/{id} 置 is_deleted=true（不物理删除，§5.1）。
#       RBAC：event:write（POST/DELETE）、event:read（GET），deny → ForbiddenError（403）。
#       审计：mutating 操作接 AuditService 留痕（§10.4；与 EventService 共享请求 session，避免 T008 不一致窗口）。
# 边界：路由不感知 DB；业务规则在 EventService；RBAC 判定在 AuthService.authorize。

"""Events API 路由（创建 / 查询 / 纠错 / 软删除）。

端点（前缀 ``/api/v1/events``，架构 §15.2）：
    - ``POST /events``：创建事件（event_id 幂等，架构 §505；需 event:write）。
    - ``GET /events``：查询事件时间线（按 baby_id/family_id/event_type 过滤，§6.1 索引；需 event:read）。
    - ``POST /events/{event_id}/correct``：纠错（correction 链，§5.1；需 event:write）。
    - ``DELETE /events/{event_id}``：软删除（is_deleted=true，不物理删除，§5.1；需 event:write）。

mutating 操作（POST/DELETE/correct）接 ``AuditService`` 留痕（§10.4 不可绕过）。
``AuditService`` 与 ``EventService`` 共享同一请求 session（``get_event_service_dep`` 一并构造），
避免 T008 阶段 audit 与业务跨 session 的不一致窗口。
路由只做 HTTP 适配；业务规则在 ``EventService``；RBAC 在 ``AuthService.authorize``（架构 §5 分层）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from pydantic import BaseModel, ConfigDict, Field

from ...auth.domain import Principal
from ...auth.service.auth_service import AuthService
from ...di import EventContext, get_event_context_dep, get_principal_dep
from ..domain import ObservationEvent, ProcessingStatus, Source, SyncStatus

router = APIRouter(prefix="/api/v1/events", tags=["events"])

# 依赖别名（Annotated 风格，避免 ruff B008，FastAPI 推荐写法）。
# EventContextDep 单次注入即提供 EventService + AuditService（共享同一请求 session，
# 避免 audit 与 event 跨 session 的不一致窗口，§10.4）。
EventContextDep = Annotated[EventContext, Depends(get_event_context_dep)]
PrincipalDep = Annotated[Principal, Depends(get_principal_dep)]


# ---- 请求/响应模型 ----


class CreateEventRequest(BaseModel):
    """创建事件请求（同步契约字段，架构 §6.3）。

    ``event_id`` 由客户端生成（ULID，幂等键，架构铁律 8 离线记录不丢失）；
    ``server_received_at`` 由服务端填充（不接受客户端覆盖，§6.3）。
    """

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(description="事件 ULID（客户端生成，幂等键）")
    baby_id: str = Field(description="婴儿 ULID")
    family_id: str = Field(description="家庭 ULID")
    event_type: str = Field(description="事件类型（如 feeding/diaper/sleep/temperature）")
    start_time: datetime = Field(description="事件开始时间（UTC aware）")
    client_created_at: datetime = Field(description="客户端创建时间（UTC aware）")
    normalized_payload: dict = Field(description="归一化载荷（结构化）")
    source: Source = Field(description="事件来源（架构 §6.2/§6.3）")
    user_id: str | None = Field(default=None, description="记录者 ULID")
    device_id: str | None = Field(default=None, description="设备 ULID")
    end_time: datetime | None = Field(default=None, description="事件结束时间")
    raw_input: dict | None = Field(default=None, description="原始输入（可能含 PII）")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度")
    attachments: list[str] = Field(default_factory=list, description="附件 ULID 列表")
    sync_status: SyncStatus = Field(default=SyncStatus.PENDING, description="同步状态")
    processing_status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING, description="归一化流水线状态"
    )


class CorrectEventRequest(BaseModel):
    """纠错请求（correction 链，架构 §5.1）。

    创建一条新事件，``correction_of`` 指向路径中的 ``event_id``（旧事件被软删除）。
    新事件 ``event_id`` 由服务端生成。
    """

    model_config = ConfigDict(extra="forbid")

    baby_id: str = Field(description="婴儿 ULID")
    family_id: str = Field(description="家庭 ULID")
    event_type: str = Field(description="事件类型")
    start_time: datetime = Field(description="事件开始时间（UTC aware）")
    client_created_at: datetime = Field(description="客户端创建时间（UTC aware）")
    normalized_payload: dict = Field(description="归一化载荷（纠正后内容）")
    source: Source = Field(description="事件来源")
    user_id: str | None = Field(default=None, description="记录者 ULID")
    device_id: str | None = Field(default=None, description="设备 ULID")
    end_time: datetime | None = Field(default=None, description="事件结束时间")
    raw_input: dict | None = Field(default=None, description="原始输入")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度")
    attachments: list[str] = Field(default_factory=list, description="附件 ULID 列表")


class EventResponse(BaseModel):
    """事件响应（ObservationEvent 领域模型投影，架构 §15.2）。"""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    baby_id: str
    family_id: str
    user_id: str | None
    device_id: str | None
    event_type: str
    start_time: datetime
    end_time: datetime | None
    client_created_at: datetime
    server_received_at: datetime
    raw_input: dict | None
    normalized_payload: dict
    confidence: float
    source: Source
    attachments: list[str]
    correction_of: str | None
    is_deleted: bool
    sync_status: SyncStatus
    processing_status: ProcessingStatus

    @classmethod
    def from_domain(cls, ev: ObservationEvent) -> EventResponse:
        return cls(
            event_id=ev.event_id,
            baby_id=ev.baby_id,
            family_id=ev.family_id,
            user_id=ev.user_id,
            device_id=ev.device_id,
            event_type=ev.event_type,
            start_time=ev.start_time,
            end_time=ev.end_time,
            client_created_at=ev.client_created_at,
            server_received_at=ev.server_received_at,
            raw_input=ev.raw_input,
            normalized_payload=ev.normalized_payload,
            confidence=ev.confidence,
            source=ev.source,
            attachments=list(ev.attachments),
            correction_of=ev.correction_of,
            is_deleted=ev.is_deleted,
            sync_status=ev.sync_status,
            processing_status=ev.processing_status,
        )


# ---- 端点 ----


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EventResponse)
async def create_event(
    body: CreateEventRequest,
    principal: PrincipalDep,
    ctx: EventContextDep,
) -> EventResponse:
    """创建事件（event_id 幂等，架构 §505；需 event:write）。

    重复提交同一 ``event_id`` 返回既有记录（不创建重复行、不抛 ConflictError）。
    """
    AuthService.authorize(principal, "event:write")
    ev = await ctx.event_service.record(
        event_id=body.event_id,
        baby_id=body.baby_id,
        family_id=body.family_id,
        event_type=body.event_type,
        start_time=body.start_time,
        client_created_at=body.client_created_at,
        normalized_payload=body.normalized_payload,
        source=body.source,
        user_id=body.user_id,
        device_id=body.device_id,
        end_time=body.end_time,
        raw_input=body.raw_input,
        confidence=body.confidence,
        attachments=body.attachments,
        sync_status=body.sync_status,
        processing_status=body.processing_status,
        audit=ctx.audit_service,
    )
    return EventResponse.from_domain(ev)


@router.get("", response_model=list[EventResponse])
async def list_events(
    principal: PrincipalDep,
    ctx: EventContextDep,
    baby_id: Annotated[str | None, Query(description="按婴儿 ULID 过滤")] = None,
    family_id: Annotated[str | None, Query(description="按家庭 ULID 过滤")] = None,
    event_type: Annotated[str | None, Query(description="按事件类型过滤")] = None,
    limit: Annotated[int, Query(ge=1, le=500, description="返回上限")] = 100,
) -> list[EventResponse]:
    """查询事件时间线（按 start_time DESC，§6.1 索引；需 event:read）。

    默认排除软删除事件（架构 §5.1；审计可追溯，§10.4）。
    """
    AuthService.authorize(principal, "event:read")
    events = await ctx.event_service.list_events(
        baby_id=baby_id,
        family_id=family_id,
        event_type=event_type,
        limit=limit,
    )
    return [EventResponse.from_domain(e) for e in events]


@router.post("/{event_id}/correct", response_model=EventResponse)
async def correct_event(
    body: CorrectEventRequest,
    principal: PrincipalDep,
    ctx: EventContextDep,
    event_id: Annotated[str, Path(description="被纠正事件 ULID")],
) -> EventResponse:
    """纠错事件（correction 链，§5.1；需 event:write）。

    软删除旧事件 + 新事件 ``correction_of`` 指向旧 event_id（不覆盖历史）。
    """
    AuthService.authorize(principal, "event:write")
    ev = await ctx.event_service.correct(
        correction_of=event_id,
        baby_id=body.baby_id,
        family_id=body.family_id,
        event_type=body.event_type,
        start_time=body.start_time,
        client_created_at=body.client_created_at,
        normalized_payload=body.normalized_payload,
        source=body.source,
        user_id=body.user_id,
        device_id=body.device_id,
        end_time=body.end_time,
        raw_input=body.raw_input,
        confidence=body.confidence,
        attachments=body.attachments,
        audit=ctx.audit_service,
    )
    return EventResponse.from_domain(ev)


@router.delete("/{event_id}", response_model=EventResponse)
async def delete_event(
    principal: PrincipalDep,
    ctx: EventContextDep,
    event_id: Annotated[str, Path(description="事件 ULID")],
) -> EventResponse:
    """软删除事件（is_deleted=true，不物理删除，§5.1；需 event:write）。"""
    AuthService.authorize(principal, "event:write")
    ev = await ctx.event_service.soft_delete(event_id=event_id, audit=ctx.audit_service)
    return EventResponse.from_domain(ev)

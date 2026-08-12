# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/events/domain/observation_event.py —— ObservationEvent 领域契约与仓储协议。
# 依据：ENGINEERING_DESIGN §5.1（ObservationEvent 数据契约 SSOT，架构 §6.2/§6.3）、
#       §5.2（Repository Protocol + 请求作用域 + 事务边界在 service）、§6.2（双状态字段）、§9.1（异常）；
#       ARCHITECTURE_FINAL §6.2（统一事件模型）、§6.3（同步记录契约）、§5.1（事件生命周期）；
#       TASK_BACKLOG APC-T009（Source 枚举；区分 sync_status/processing_status；
#       重复 event_id 不创建重复记录；correction_of 与 is_deleted 保留）。
# 设计：领域层纯数据契约 + Protocol，不感知 HTTP/DB（架构 §5：Protocol + Pydantic 模型）。
#       ObservationEvent 为事件溯源核心（架构 §6.2），所有输入先归一为此模型。
#       双状态字段（§6.2）：sync_status(同步状态) 与 processing_status(归一化流水线状态)
#       独立推进——sync_status 由 PowerSync 上行推进，processing_status 由 normalization 推进。
#       枚举值严格对齐 ORM CHECK 约束（models/events.py），避免写入被 DB 拒绝。
# 边界：domain 不含实现（DB 访问在 infra/repository；幂等策略在 service/idempotency）；
#       异常复用 common/errors（ConflictError/NotFoundError/ValidationError）。

"""ObservationEvent 领域契约与仓储协议（事件溯源核心）。

架构（ENGINEERING_DESIGN §5.1 / §6.2 / ARCHITECTURE_FINAL §6.2/§6.3）：
所有输入（manual/voice_text/camera/sensor/ai/system）先归一为 ``ObservationEvent``，
它是事件溯源的核心数据契约。领域派生表（feeding_log/diaper_log 等）由其归一化生成。

双状态字段（§6.2）—— 两条独立推进的状态机：
    ``sync_status`` —— 同步状态（PowerSync 上行）：pending → synced。
    ``processing_status`` —— 归一化流水线状态：pending → normalized → projected。
两者解耦：一个事件可先 synced 再 normalized，也可先 normalized 再 synced（崩溃恢复用
processing_status，架构 §730）。

同步记录契约（架构 §6.3）：每条可同步记录含 event_id/baby_id/family_id/user_id/
device_id/event_type/client_created_at/server_received_at/payload/source/confidence/
is_deleted/correction_of。本契约以 ``normalized_payload`` 承载 payload。

幂等（架构 §505 / TASK_BACKLOG APC-T009）：写接口以 ``event_id`` 幂等，重复提交合并——
``ObservationEventRepository.upsert`` 对已存在 event_id 返回既有记录，不创建重复行。

correction 链（§5.1 / §544）：``correction_of`` 指向被纠正事件的 event_id；
纠错流程为"软删除旧事件 + 新事件 correction_of 指向旧 event_id"，不物理删除。
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

# ---- 枚举（值严格对齐 ORM CHECK 约束 models/events.py）----


class Source(StrEnum):
    """事件来源（架构 §6.2 / §6.3 / ORM CHECK ck_observation_event_source）。

    ``StrEnum``：与 ORM ``source``（``String(16)``）直接互转，避免额外映射层。
    """

    MANUAL = "manual"
    VOICE_TEXT = "voice_text"
    CAMERA = "camera"
    SENSOR = "sensor"
    AI = "ai"
    SYSTEM = "system"


class SyncStatus(StrEnum):
    """同步状态（PowerSync 上行，架构 §6.2 / ORM CHECK ck_observation_event_sync_status）。

    ``pending`` —— 客户端已记录、尚未确认上行到 PostgreSQL 权威源。
    ``synced`` —— 已上行到 PostgreSQL（权威源，架构 §6 M1 硬事实）。
    """

    PENDING = "pending"
    SYNCED = "synced"


class ProcessingStatus(StrEnum):
    """归一化流水线状态（架构 §6.2 / ORM CHECK ck_observation_event_processing_status）。

    ``pending`` —— 原始事件，尚未归一化。
    ``normalized`` —— 已归一化（normalized_payload 已填充/校验）。
    ``projected`` —— 已投影到派生表（state_engine 增量重算完成）。

    注：ENGINEERING_DESIGN §5.1 文本示例写作 ``raw|normalized|derived``，但 §6.2 与
    ORM（已迁移落地，T004）统一为 ``pending|normalized|projected``。以 ORM 为 SSOT
    （DB CHECK 约束已固化），避免写入被拒。
    """

    PENDING = "pending"
    NORMALIZED = "normalized"
    PROJECTED = "projected"


# ---- 数据契约（§5.1 SSOT）----


class ObservationEvent(BaseModel):
    """ObservationEvent 数据契约（事件溯源核心，§5.1 SSOT）。

    字段对齐 §5.1：
        event_id, baby_id, family_id, user_id, device_id, event_type,
        start_time, end_time, client_created_at, server_received_at,
        raw_input, normalized_payload, confidence, source, attachments,
        correction_of, is_deleted。

    双状态字段（§6.2）：``sync_status`` / ``processing_status`` 独立推进。
    ``correction_of`` 指向被纠正事件（correction 链，不物理删除）。
    ``is_deleted`` 软删除标志（架构 §5.1：不物理删除，配合 partial index）。

    ``event_id`` 为幂等键（架构 §505）：重复 upsert 返回既有记录，不创建重复行。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(description="事件 ULID（幂等键，应用层生成）")
    baby_id: str = Field(description="婴儿 ULID（baby.id）")
    family_id: str = Field(description="家庭 ULID（family.id）")
    user_id: str | None = Field(
        default=None, description="记录者 ULID（user.id）；System/设备自动写入时为 None"
    )
    device_id: str | None = Field(
        default=None, description="设备 ULID（device.id）；手动记录时为 None"
    )
    event_type: str = Field(description="事件类型（如 feeding/diaper/sleep/temperature）")
    start_time: datetime = Field(description="事件开始时间（UTC aware）")
    end_time: datetime | None = Field(
        default=None, description="事件结束时间（UTC aware）；瞬时事件为 None"
    )
    client_created_at: datetime = Field(
        description="客户端创建时间（UTC aware，同步契约字段，架构 §6.3）"
    )
    server_received_at: datetime = Field(
        description="服务端接收时间（UTC aware，同步契约字段，架构 §6.3）"
    )
    raw_input: dict[str, Any] | None = Field(
        default=None, description="原始输入（语音文本/图片/OCR/表单），可能含 PII"
    )
    normalized_payload: dict[str, Any] = Field(description="归一化载荷（结构化，payload 承载处）")
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="置信度（0.0-1.0，manual=1.0）"
    )
    source: Source = Field(description="事件来源（架构 §6.2/§6.3）")
    attachments: list[str] = Field(default_factory=list, description="附件 media_asset ULID 列表")
    correction_of: str | None = Field(
        default=None, description="被纠正事件的 event_id（correction 链，§5.1）"
    )
    is_deleted: bool = Field(default=False, description="软删除标志（不物理删除，§5.1）")
    sync_status: SyncStatus = Field(
        default=SyncStatus.PENDING, description="同步状态（PowerSync 上行，§6.2）"
    )
    processing_status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING,
        description="归一化流水线状态（§6.2，崩溃恢复用，架构 §730）",
    )


# ---- 仓储协议（§5.2 Repository Protocol）----


@runtime_checkable
class ObservationEventRepository(Protocol):
    """ObservationEvent 仓储协议（架构 §5.2）。

    生命周期：请求作用域（FastAPI ``Depends`` 注入 session）；事务边界在 service 层。
    实现见 ``events.infra.repository.SqlAlchemyObservationEventRepository``。

    幂等（TASK_BACKLOG APC-T009 / 架构 §505）：``upsert`` 以 ``event_id`` 为幂等键，
    重复提交返回既有记录（不创建重复行，不抛 ConflictError）。
    """

    async def get(self, event_id: str) -> ObservationEvent | None:
        """按 event_id 取未删除事件（软删除过滤）。"""
        ...

    async def upsert(self, entity: ObservationEvent) -> ObservationEvent:
        """幂等写入：event_id 已存在则返回既有记录，否则插入新记录。

        幂等语义（架构 §505）：重复提交合并，不创建重复 event_id 行。
        """
        ...

    async def query(
        self,
        *,
        baby_id: str | None = None,
        family_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[ObservationEvent]:
        """按过滤条件查询未删除事件（按 start_time DESC）。"""
        ...

    async def soft_delete(self, event_id: str) -> ObservationEvent | None:
        """软删除事件（置 is_deleted=true，不物理删除，§5.1）。

        返回更新后的事件；不存在则返回 None。
        """
        ...

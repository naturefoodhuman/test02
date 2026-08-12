# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/sync/service/contract_validator.py —— PowerSync 同步契约校验（APC-T012）。
# 依据：ENGINEERING_DESIGN §6.3（同步记录契约字段）、§9.1（不自研同步引擎，PowerSync 复用）；
#       ARCHITECTURE_FINAL §9.2（同步与冲突规则）、§6.3（同步记录契约）；
#       TASK_BACKLOG APC-T012（校验每条同步记录含架构 §6.3 字段；非法同步事件不进入业务处理；
#       pending_sync 与 processing_status 独立推进）。
# 设计：PowerSync 上行记录先经契约校验，缺字段 → ValidationError（400），不进入 EventService。
#       同步契约字段（§6.3）：event_id/baby_id/family_id/user_id/device_id/event_type/
#       client_created_at/server_received_at/payload/source/confidence/is_deleted/correction_of。
#       ``payload``（§6.3 契约名）映射到 ObservationEvent.normalized_payload（§5.1 领域名）。
#       server_received_at 由服务端覆盖（§6.3 服务端权威），不接受客户端值。
# 边界：只做契约校验与字段映射，不含业务规则（幂等/纠错在 EventService）；
#       不自研同步引擎（PowerSync 复用，架构 §9.1）。

"""PowerSync 同步契约校验（APC-T012）。

架构（ENGINEERING_DESIGN §6.3 / §9.1 / ARCHITECTURE_FINAL §9.2）：
PowerSync 上行记录（Android SQLite → PowerSync → PG）先经契约校验，确保含 §6.3 同步契约
字段。非法记录 → ``ValidationError``（400），不进入 ``EventService``（验收：非法同步事件
不会进入业务处理）。

同步契约字段（§6.3）：
    event_id, baby_id, family_id, user_id, device_id, event_type,
    client_created_at, server_received_at, payload, source,
    confidence, is_deleted, correction_of。

字段映射：
    ``payload``（§6.3 契约名）→ ``normalized_payload``（§5.1 领域名）。
    ``server_received_at`` 由服务端覆盖（§6.3 服务端权威接收时间），不接受客户端值。
    ``sync_status`` 上行成功即 ``synced``（架构 §6.2：pending → synced）。

pending_sync 与 processing_status 独立（APC-T012）：上行成功 → sync_status=synced，
但 processing_status 仍为 pending（归一化 worker 推进），两条状态机独立（§6.2）。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ...common.errors import ValidationError
from ...common.ids import is_valid_ulid
from ...events.domain import ObservationEvent, ProcessingStatus, Source, SyncStatus

# §6.3 同步契约必填字段（user_id/device_id/end_time 可空，不计入必填）。
_REQUIRED_CONTRACT_FIELDS = (
    "event_id",
    "baby_id",
    "family_id",
    "event_type",
    "client_created_at",
    "payload",
    "source",
)

# source 合法值（与 Source 枚举 / ORM CHECK 对齐）。
_VALID_SOURCES = {s.value for s in Source}


def validate_sync_contract(record: dict[str, Any]) -> ObservationEvent:
    """校验 PowerSync 上行记录是否符合 §6.3 同步契约，返回 ObservationEvent 领域模型。

    Args:
        record: PowerSync 上行的原始记录（dict，含 §6.3 契约字段）。

    Returns:
        校验通过后的 ``ObservationEvent``（sync_status=synced，processing_status=pending）。

    Raises:
        ValidationError: 缺必填字段 / ULID 非法 / source 非法 / confidence 越界 /
            payload 非 dict。非法记录不进入 EventService（验收：非法同步事件不进入业务）。
    """
    if not isinstance(record, dict):
        raise ValidationError("Sync record must be a JSON object")

    # 1. 必填字段检查。
    missing = [f for f in _REQUIRED_CONTRACT_FIELDS if f not in record]
    if missing:
        raise ValidationError(
            "Sync record missing required contract fields",
            evidence={"missing": missing},
        )

    # 2. ULID 校验（event_id/baby_id/family_id）。
    for field in ("event_id", "baby_id", "family_id"):
        if not is_valid_ulid(record[field]):
            raise ValidationError(f"Invalid ULID for {field}", evidence={field: record[field]})

    # 3. source 合法性。
    source_raw = record["source"]
    if source_raw not in _VALID_SOURCES:
        raise ValidationError(
            f"Invalid source, must be one of {sorted(_VALID_SOURCES)}",
            evidence={"source": source_raw},
        )

    # 4. payload 必须是 dict（映射到 normalized_payload）。
    payload = record["payload"]
    if not isinstance(payload, dict):
        raise ValidationError(f"payload must be a JSON object, got {type(payload).__name__}")

    # 5. confidence 越界检查（可选字段，默认 1.0）。
    confidence = record.get("confidence", 1.0)
    if not isinstance(confidence, int | float) or not (0.0 <= confidence <= 1.0):
        raise ValidationError(
            "confidence must be in [0.0, 1.0]", evidence={"confidence": confidence}
        )

    # 6. 构造 ObservationEvent（server_received_at 由服务端覆盖，sync_status=synced）。
    # start_time 可选，缺失则回退到 client_created_at（必填，required=True 缺失即抛异常）。
    start_time = _parse_dt(record, "start_time", required=False) or _parse_dt(
        record, "client_created_at", required=True
    )
    client_created_at = _parse_dt(record, "client_created_at", required=True)
    assert start_time is not None  # client_created_at required=True 缺失已抛异常
    assert client_created_at is not None
    return ObservationEvent(
        event_id=record["event_id"],
        baby_id=record["baby_id"],
        family_id=record["family_id"],
        user_id=record.get("user_id"),
        device_id=record.get("device_id"),
        event_type=record["event_type"],
        start_time=start_time,
        end_time=_parse_dt(record, "end_time", required=False),
        client_created_at=client_created_at,
        # server_received_at 由 EventService.record 用 Clock 覆盖；此处占位，service 会重置。
        server_received_at=datetime.fromtimestamp(0, tz=UTC),
        raw_input=record.get("raw_input"),
        normalized_payload=payload,
        confidence=float(confidence),
        source=Source(source_raw),
        attachments=record.get("attachments", []) or [],
        correction_of=record.get("correction_of"),
        is_deleted=bool(record.get("is_deleted", False)),
        # 上行成功 → synced；processing_status=pending（归一化 worker 推进，独立状态机）。
        sync_status=SyncStatus.SYNCED,
        processing_status=ProcessingStatus.PENDING,
    )


def _parse_dt(record: dict[str, Any], field: str, *, required: bool) -> datetime | None:
    """从 record 解析 datetime 字段（ISO 字符串或 datetime）。"""
    if field not in record or record[field] is None:
        if required:
            raise ValidationError(f"Missing required datetime field: {field}")
        return None
    value = record[field]
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValidationError(
                f"Invalid ISO datetime for {field}", evidence={field: value}
            ) from exc
    raise ValidationError(
        f"{field} must be ISO datetime string or datetime, got {type(value).__name__}"
    )


__all__ = ["validate_sync_contract"]

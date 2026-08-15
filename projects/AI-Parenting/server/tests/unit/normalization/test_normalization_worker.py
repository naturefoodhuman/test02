# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-15 00:00:00
"""NormalizationWorker 单元测试（APC-T014）。

用内存 ``WorkerContext`` 替身验证 worker 的 op 分发 / 去重 / 纠错链 / 软删除 / 异常隔离
逻辑，不依赖 DB（DB 链路在 integration 测试覆盖）。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from server.app.events.domain import (
    ObservationEvent,
    ProcessingStatus,
    Source,
    SyncStatus,
)
from server.app.normalization.worker import NormalizationWorker

NOW = datetime(2026, 8, 15, 8, 0, 0, tzinfo=UTC)
EID = "01HZXKQW7P0QJ9V8R3M4N6H5T2"
OLD_EID = "01HZXKQW7P0QJ9V8R3M4N6H5T9"
BABY = "01HZXKQW7P0QJ9V8R3M4N6H5T3"
FAM = "01HZXKQW7P0QJ9V8R3M4N6H5T4"


class FakeWorkerContext:
    """内存 WorkerContext 替身，记录所有调用。"""

    def __init__(
        self,
        _session: Any = None,
        *,
        event: ObservationEvent | None = None,
        events: dict[str, ObservationEvent] | None = None,
        normalize_raises: type[Exception] | None = None,
    ) -> None:
        self._event = event
        self._events: dict[str, ObservationEvent] = events or {}
        self.soft_deleted: list[str] = []  # 被软删除派生行的 event_id 列表
        self.normalized: list[ObservationEvent] = []
        self.commits = 0
        self.normalize_raises = normalize_raises

    async def get_event(self, event_id: str) -> ObservationEvent | None:
        if self._events:
            return self._events.get(event_id)
        if self._event is not None and event_id == self._event.event_id:
            return self._event
        return None

    async def soft_delete_event_logs(self, event_id: str) -> None:
        self.soft_deleted.append(event_id)

    async def normalize(self, event: ObservationEvent) -> None:
        if self.normalize_raises is not None:
            raise self.normalize_raises("normalize failed")
        self.normalized.append(event)

    async def commit(self) -> None:
        self.commits += 1


def _feeding_event(
    *,
    event_id: str = EID,
    processing_status: ProcessingStatus = ProcessingStatus.PENDING,
    correction_of: str | None = None,
    is_deleted: bool = False,
) -> ObservationEvent:
    return ObservationEvent(
        event_id=event_id,
        baby_id=BABY,
        family_id=FAM,
        event_type="feeding",
        start_time=NOW,
        client_created_at=NOW,
        server_received_at=NOW,
        normalized_payload={"amount_ml": 120},
        source=Source.MANUAL,
        sync_status=SyncStatus.SYNCED,
        processing_status=processing_status,
        correction_of=correction_of,
        is_deleted=is_deleted,
    )


def _make_worker(ctx: FakeWorkerContext) -> NormalizationWorker:
    """构造注入内存 context 的 worker。

    session_factory 用一个返回占位 session 的假工厂（FakeWorkerContext 忽略 session 参数）。
    """
    class _FakeSessionFactory:
        def __call__(self) -> _FakeSessionFactory:
            return self

        async def __aenter__(self) -> object:
            return object()  # 占位 session，FakeWorkerContext 不使用。

        async def __aexit__(self, *exc: object) -> None:
            return None

    return NormalizationWorker(
        session_factory=_FakeSessionFactory(),  # type: ignore[arg-type]
        context_factory=lambda _session: ctx,
    )


async def test_insert_normalizes_and_commits():
    ctx = FakeWorkerContext(event=_feeding_event())
    worker = _make_worker(ctx)

    await worker.handle({"event_id": EID, "op": "insert"})

    assert len(ctx.normalized) == 1
    assert ctx.normalized[0].event_id == EID
    assert ctx.commits == 1
    assert ctx.soft_deleted == []  # 无纠错链。


async def test_update_and_recover_route_to_upsert():
    ctx = FakeWorkerContext(event=_feeding_event())
    worker = _make_worker(ctx)

    await worker.handle({"event_id": EID, "op": "update"})
    assert len(ctx.normalized) == 1
    await worker.handle({"event_id": EID, "op": "recover"})
    # 第二次因 processing_status 已被 normalize 推进？FakeWorkerContext 不改 status，
    # 故仍会 normalize（验证路由，不验证去重——去重在下一例）。
    assert len(ctx.normalized) == 2


async def test_dedup_skips_already_normalized():
    ev = _feeding_event(processing_status=ProcessingStatus.NORMALIZED)
    ctx = FakeWorkerContext(event=ev)
    worker = _make_worker(ctx)

    await worker.handle({"event_id": EID, "op": "insert"})

    assert ctx.normalized == []
    assert ctx.commits == 0


async def test_dedup_skips_projected():
    ev = _feeding_event(processing_status=ProcessingStatus.PROJECTED)
    ctx = FakeWorkerContext(event=ev)
    worker = _make_worker(ctx)

    await worker.handle({"event_id": EID, "op": "recover"})

    assert ctx.normalized == []
    assert ctx.commits == 0


async def test_correction_chain_soft_deletes_old_logs_first():
    ev = _feeding_event(correction_of=OLD_EID)
    ctx = FakeWorkerContext(event=ev)
    worker = _make_worker(ctx)

    await worker.handle({"event_id": EID, "op": "insert"})

    # 先软删除旧 event_id 派生行，再 normalize 新事件。
    assert ctx.soft_deleted == [OLD_EID]
    assert len(ctx.normalized) == 1
    assert ctx.normalized[0].event_id == EID


async def test_delete_soft_deletes_logs_no_normalize():
    ctx = FakeWorkerContext()
    worker = _make_worker(ctx)

    await worker.handle({"event_id": EID, "op": "delete"})

    assert ctx.soft_deleted == [EID]
    assert ctx.normalized == []
    assert ctx.commits == 1


async def test_event_not_found_skips():
    ctx = FakeWorkerContext(event=None)
    worker = _make_worker(ctx)

    await worker.handle({"event_id": EID, "op": "insert"})

    assert ctx.normalized == []
    assert ctx.soft_deleted == []
    assert ctx.commits == 0


async def test_missing_event_id_skips():
    ctx = FakeWorkerContext(event=_feeding_event())
    worker = _make_worker(ctx)

    await worker.handle({"op": "insert"})  # 无 event_id。
    await worker.handle({})  # 空 payload。

    assert ctx.normalized == []
    assert ctx.commits == 0


async def test_normalize_exception_isolated_does_not_raise():
    ctx = FakeWorkerContext(event=_feeding_event(), normalize_raises=RuntimeError)
    worker = _make_worker(ctx)

    # 异常被 worker 捕获，不向上抛（避免阻断消费循环）。
    await worker.handle({"event_id": EID, "op": "insert"})

    assert ctx.commits == 0  # normalize 抛异常前未 commit。


async def test_unknown_op_routes_to_upsert():
    """未知 op 一律按 upsert 处理（保守补处理，APC-T014）。"""
    ctx = FakeWorkerContext(event=_feeding_event())
    worker = _make_worker(ctx)

    await worker.handle({"event_id": EID, "op": "weird_op"})

    assert len(ctx.normalized) == 1

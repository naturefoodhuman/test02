# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 07:15:00


"""Sleep Session state machine and dev repository."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from server.app.camera.roi import ROIConfig
from server.app.common.clock import utc_now
from server.app.common.errors import ConflictError, NotFoundError
from server.app.common.ids import new_ulid
from server.app.observability.audit import AuditActor, AuditRecord, AuditSink


class SleepSessionState(StrEnum):
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


class SleepSessionRecord(BaseModel):
    id: str = Field(default_factory=new_ulid)
    baby_id: str
    family_id: str
    state: SleepSessionState = SleepSessionState.ACTIVE
    started_at: str = Field(default_factory=lambda: utc_now().isoformat())
    ended_at: str | None = None
    roi_config: dict[str, float] = Field(default_factory=dict)

    @property
    def analysis_allowed(self) -> bool:
        return self.state == SleepSessionState.ACTIVE


class InMemorySleepSessionRepository:
    def __init__(self, audit_sink: AuditSink | None = None) -> None:
        self.sessions: dict[str, SleepSessionRecord] = {}
        self.audit_sink = audit_sink

    async def start(self, *, baby_id: str, family_id: str) -> SleepSessionRecord:
        session = SleepSessionRecord(baby_id=baby_id, family_id=family_id)
        self.sessions[session.id] = session
        await self._audit("sleep_session.start", session)
        return session

    async def get(self, session_id: str) -> SleepSessionRecord:
        session = self.sessions.get(session_id)
        if session is None:
            raise NotFoundError("Sleep session not found", evidence={"session_id": session_id})
        return session

    async def pause(self, session_id: str) -> SleepSessionRecord:
        session = await self.get(session_id)
        if session.state != SleepSessionState.ACTIVE:
            raise ConflictError("Only active sleep sessions can be paused")
        session.state = SleepSessionState.PAUSED
        await self._audit("sleep_session.pause", session)
        return session

    async def resume(self, session_id: str) -> SleepSessionRecord:
        session = await self.get(session_id)
        if session.state != SleepSessionState.PAUSED:
            raise ConflictError("Only paused sleep sessions can be resumed")
        session.state = SleepSessionState.ACTIVE
        await self._audit("sleep_session.resume", session)
        return session

    async def end(self, session_id: str) -> SleepSessionRecord:
        session = await self.get(session_id)
        if session.state == SleepSessionState.ENDED:
            raise ConflictError("Sleep session is already ended")
        session.state = SleepSessionState.ENDED
        session.ended_at = utc_now().isoformat()
        await self._audit("sleep_session.end", session)
        return session

    async def set_roi(self, session_id: str, roi: ROIConfig) -> SleepSessionRecord:
        session = await self.get(session_id)
        session.roi_config = roi.as_dict()
        await self._audit("sleep_session.roi_update", session)
        return session

    async def _audit(self, action: str, session: SleepSessionRecord) -> None:
        if self.audit_sink is None:
            return
        await self.audit_sink.record(
            AuditRecord(
                actor=AuditActor(actor_kind="system"),
                action=action,
                resource=f"sleep_session:{session.id}",
                after=session.model_dump(mode="json"),
            )
        )

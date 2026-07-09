# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 12:50:00


"""Normalization service with in-memory derived table writer."""

from __future__ import annotations

from pydantic import BaseModel, Field

from server.app.common.clock import utc_now
from server.app.common.ids import new_ulid
from server.app.events.domain.observation_event import ObservationEvent, ProcessingStatus
from server.app.normalization.parsers.form import parse_form_event
from server.app.normalization.parsers.voice import parse_voice_text


class NormalizedRecord(BaseModel):
    id: str = Field(default_factory=new_ulid)
    event_id: str
    baby_id: str
    family_id: str
    record_type: str
    payload: dict[str, object] = Field(default_factory=dict)
    confidence: float = 1.0
    is_deleted: bool = False
    correction_of: str | None = None
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class InMemoryDerivedTableStore:
    def __init__(self) -> None:
        self.records_by_event: dict[str, NormalizedRecord] = {}

    def upsert(self, record: NormalizedRecord) -> NormalizedRecord:
        existing = self.records_by_event.get(record.event_id)
        if existing is not None:
            return existing
        self.records_by_event[record.event_id] = record
        return record

    def list_by_baby(
        self,
        baby_id: str,
        *,
        include_deleted: bool = False,
    ) -> list[NormalizedRecord]:
        rows = [record for record in self.records_by_event.values() if record.baby_id == baby_id]
        if not include_deleted:
            rows = [record for record in rows if not record.is_deleted]
        return rows


class NormalizationService:
    def __init__(self, store: InMemoryDerivedTableStore | None = None) -> None:
        self.store = store or InMemoryDerivedTableStore()

    def normalize(self, event: ObservationEvent) -> NormalizedRecord | None:
        if event.is_deleted:
            event.processing_status = ProcessingStatus.NORMALIZED
            return None
        if event.source == "voice_text" and event.raw_input.get("text"):
            record_type, payload, confidence = parse_voice_text(str(event.raw_input["text"]))
        else:
            record_type, payload, confidence = parse_form_event(event)
        if record_type == "unknown":
            event.processing_status = ProcessingStatus.NORMALIZED
            return None
        record = self.store.upsert(
            NormalizedRecord(
                event_id=event.event_id,
                baby_id=event.baby_id,
                family_id=event.family_id,
                record_type=record_type,
                payload=payload,
                confidence=confidence,
                correction_of=event.correction_of,
            )
        )
        event.processing_status = ProcessingStatus.NORMALIZED
        return record

    def scan_pending(self, events: list[ObservationEvent]) -> list[NormalizedRecord]:
        records: list[NormalizedRecord] = []
        for event in events:
            if event.processing_status == ProcessingStatus.PENDING:
                record = self.normalize(event)
                if record is not None:
                    records.append(record)
        return records

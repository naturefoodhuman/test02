# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 02:50:00


"""EvidencePolicy repository abstractions."""

from __future__ import annotations

from dataclasses import dataclass

from server.app.common.clock import utc_now
from server.app.rule_engine.loader import RulePack


@dataclass(slots=True)
class EvidencePolicyRecord:
    policy_type: str
    region: str
    version: str
    effective_from: str
    source: str
    rule_text: str
    hash: str
    effective_to: str | None = None


class InMemoryEvidencePolicyRepository:
    """In-memory policy repo until PostgreSQL-backed EvidencePolicy repo lands."""

    def __init__(self) -> None:
        self.records: list[EvidencePolicyRecord] = []
        self._cache: dict[tuple[str, str], EvidencePolicyRecord] = {}

    def activate(self, pack: RulePack) -> EvidencePolicyRecord:
        key = (pack.policy_type, pack.region)
        current = self._cache.get(key)
        if current is not None:
            current.effective_to = utc_now().isoformat()
        record = EvidencePolicyRecord(
            policy_type=pack.policy_type,
            region=pack.region,
            version=pack.version,
            effective_from=pack.effective_from,
            source=pack.source,
            rule_text=pack.model_dump_json(exclude={"hash"}),
            hash=pack.compute_hash(),
        )
        self.records.append(record)
        self._cache[key] = record
        return record

    def get_current(self, policy_type: str, region: str = "CN") -> EvidencePolicyRecord | None:
        return self._cache.get((policy_type, region))

    def invalidate(self, policy_type: str, region: str = "CN") -> None:
        self._cache.pop((policy_type, region), None)

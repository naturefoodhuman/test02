# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Evidence collection service."""

from __future__ import annotations

from pydantic import Field

from _infra.feos.models import Evidence, EvidenceContent, EvidenceQuality, EvidenceRelations, EvidenceSecurity, EvidenceSource, TimelineEvent
from _infra.feos.models.base import FEOSModel
from _infra.feos.models.ids import FEOSIdGenerator
from _infra.feos.ports.collectors import EvidenceCollectionRequest
from _infra.feos.repositories import ArtifactRepository, TimelineRepository
from _infra.feos.storage import FEOSWorkspace

from .importance import importance_for_type
from .normalizer import EvidenceNormalizer
from .registry import CollectorRegistry


class EvidenceCollectionResult(FEOSModel):
    ok: bool
    evidence: list[Evidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class EvidenceService:
    def __init__(self, workspace: FEOSWorkspace, registry: CollectorRegistry, timeline_repository: TimelineRepository | None = None, id_generator: FEOSIdGenerator | None = None):
        self.workspace = workspace
        self.registry = registry
        self.timeline_repository = timeline_repository
        self.ids = id_generator or FEOSIdGenerator()
        self.normalizer = EvidenceNormalizer()
        self.repo = ArtifactRepository(workspace, "evidence")

    def collect(self, request: EvidenceCollectionRequest, enabled_collectors: list[str] | None = None) -> EvidenceCollectionResult:
        warnings = []
        errors = []
        saved: list[Evidence] = []
        collectors = self.registry.enabled_collectors(request, enabled_collectors)
        for collector in collectors:
            try:
                items = collector.collect(request)
            except Exception as exc:
                message = f"collector {collector.collector_id} failed: {exc}"
                if getattr(collector, "required", False):
                    errors.append(message)
                else:
                    warnings.append(message)
                continue
            for item in items:
                ev_id = self.ids.evidence_id("ev")
                raw = item.raw_content.encode("utf-8")
                raw_result = self.repo.put_raw(request.case_id, f"raw/{ev_id}", raw, ".txt")
                preview, normalized = self.normalizer.normalize(item)
                evidence = Evidence(
                    id=ev_id,
                    case_id=request.case_id,
                    type=item.evidence_type,
                    subtype=item.subtype,
                    source=EvidenceSource(collector=item.collector_id, origin=item.origin),
                    content=EvidenceContent(raw_ref=raw_result.ref, text_preview=preview, normalized=normalized),
                    metadata={"hash": raw_result.hash, **item.metadata},
                    quality=EvidenceQuality(importance=importance_for_type(item.evidence_type)),
                    security=EvidenceSecurity(),
                    relations=EvidenceRelations(),
                )
                self.repo.put_yaml(request.case_id, f"normalized/{ev_id}", evidence.to_dict())
                saved.append(evidence)
        if errors:
            return EvidenceCollectionResult(ok=False, evidence=saved, warnings=warnings, errors=errors)
        index = {"case_id": request.case_id, "evidence_ids": [ev.id for ev in saved]}
        self.repo.put_yaml(request.case_id, "index", index)
        if self.timeline_repository and saved:
            self.timeline_repository.append(TimelineEvent(id=self.ids.next("evt"), case_id=request.case_id, type="evidence_collected", summary=f"collected {len(saved)} evidence"))
        return EvidenceCollectionResult(ok=True, evidence=saved, warnings=warnings)

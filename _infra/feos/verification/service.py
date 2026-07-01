# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ParsedResponse, VerificationResult
from _infra.feos.repositories import VerificationRepository
from .pipeline import VerificationPipeline
from .checks.evidence_alignment_check import EvidenceAlignmentCheck
from .checks.constraint_check import ConstraintCheck
from .checks.architecture_check import ArchitectureCheck
from .checks.security_check import SecurityCheck


class VerificationService:
    def __init__(self, repository: VerificationRepository, pipeline: VerificationPipeline | None = None):
        self.repository = repository
        self.pipeline = pipeline or VerificationPipeline([EvidenceAlignmentCheck(), ConstraintCheck(), ArchitectureCheck(), SecurityCheck()])

    def verify(self, parsed: ParsedResponse, context: dict | None = None) -> VerificationResult:
        result = self.pipeline.run(parsed, context=context)
        self.repository.put_yaml(parsed.case_id, result.id, result.to_dict())
        return result

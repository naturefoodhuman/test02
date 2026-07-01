# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ParsedResponse, VerificationResult
from _infra.feos.models.ids import FEOSIdGenerator
from _infra.feos.ports.verification import VerificationCheck


class VerificationPipeline:
    def __init__(self, checks: list[VerificationCheck] | None = None, id_generator: FEOSIdGenerator | None = None):
        self.checks = checks or []
        self.ids = id_generator or FEOSIdGenerator()

    def run(self, parsed: ParsedResponse, context: dict | None = None) -> VerificationResult:
        results = []
        errors = []
        warnings = []
        for check in self.checks:
            try:
                res = check.run(parsed, context=context)
                results.append(res)
                if res.status == "failed": errors.append(res.summary or check.check_id)
                if res.status == "warning": warnings.append(res.summary or check.check_id)
            except Exception as exc:
                if getattr(check, "fatal", False):
                    errors.append(str(exc))
                else:
                    warnings.append(str(exc))
        status = "failed" if errors else ("warning" if warnings else "passed")
        return VerificationResult(id=self.ids.verification_id(), case_id=parsed.case_id, parsed_response_id=parsed.id, status=status, checks=results, warnings=warnings, errors=errors)

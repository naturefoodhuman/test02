# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ParsedResponse, Recommendation, VerificationCheckResult
from _infra.feos.repositories import VerificationRepository
from _infra.feos.storage import FEOSWorkspace, read_yaml
from _infra.feos.verification import VerificationPipeline, VerificationService


class PassCheck:
    check_id = "pass"
    fatal = False
    def run(self, parsed, context=None): return VerificationCheckResult(check_id=self.check_id, status="passed")


class FailCheck:
    check_id = "fail"
    fatal = False
    def run(self, parsed, context=None): return VerificationCheckResult(check_id=self.check_id, status="failed", summary="bad")


def test_pipeline_aggregates_and_service_saves(tmp_path):
    parsed = ParsedResponse(id="parsed", case_id="case", response_id="resp", recommendations=[Recommendation(id="rec", text="fix")])
    result = VerificationPipeline([PassCheck(), FailCheck()]).run(parsed)
    assert result.status == "failed"
    ws = FEOSWorkspace(tmp_path / "feos"); ws.ensure_initialized()
    saved = VerificationService(VerificationRepository(ws), VerificationPipeline([PassCheck()])).verify(parsed)
    assert read_yaml(ws.root / "cases" / "case" / "verification" / f"{saved.id}.yaml")["status"] == "passed"

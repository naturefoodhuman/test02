# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ParsedResponse, Recommendation
from _infra.feos.verification.checks.sandbox_check import SandboxCheck
from _infra.feos.verification.checks.testability_check import TestabilityCheck


def test_extended_checks():
    parsed = ParsedResponse(id="p", case_id="c", response_id="r", recommendations=[Recommendation(id="rec", text="change config")])
    assert TestabilityCheck().run(parsed).status == "warning"
    assert SandboxCheck().run(parsed).status == "skipped"

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.context import ContextCompiler, ContextSelector
from _infra.feos.models import CaseProblem, EscalationCase, Evidence, EvidenceContent, EvidenceQuality, EvidenceSource


def ev(ev_id, importance):
    return Evidence(id=ev_id, case_id="case_001", type="stack_trace", source=EvidenceSource(collector="c", origin="o"), content=EvidenceContent(raw_ref=f"raw/{ev_id}.txt", text_preview=ev_id), quality=EvidenceQuality(importance=importance))


def test_selector_orders_and_omits():
    selected, omitted = ContextSelector().select_evidence([ev("low", 0.1), ev("high", 0.9)], limit=1)
    assert selected[0].id == "high"
    assert omitted[0]["id"] == "low"


def test_context_compiler_sections_stable():
    case = EscalationCase(id="case_001", title="T", problem=CaseProblem(user_goal="debug"))
    ctx = ContextCompiler().compile(case, [ev("ev1", 0.9)], budget=24000)
    assert [s.id for s in ctx.sections] == ["case", "evidence", "hypotheses", "constraints"]
    assert ctx.token_estimate <= ctx.token_budget

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.context import ContextPacker, estimate_tokens
from _infra.feos.models import ContextSection


def test_token_estimate_and_budget_omission():
    assert estimate_tokens("abcd") == 1
    sections = [ContextSection(id="a", title="A", content="x" * 100), ContextSection(id="b", title="B", content="y" * 10000)]
    pkg, warnings = ContextPacker().pack("ctx_001", "case_001", sections, budget=100)
    assert pkg.sections[0].id == "a"
    assert warnings

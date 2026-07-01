# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ContextPackage, ContextSection, EscalationPackage
from _infra.feos.renderers import MarkdownRenderer


def test_clipboard_markdown_contains_stable_sections():
    md = MarkdownRenderer("generic_markdown").render(
        EscalationPackage(id="pkg", case_id="case", context_package_id="ctx"),
        ContextPackage(id="ctx", case_id="case", sections=[ContextSection(id="constraints", title="Constraints", content="Verify before execution")]),
    )
    assert md.startswith("# External Reasoning Request")
    assert "## 1. Role" in md
    assert "## Required Response Format" in md

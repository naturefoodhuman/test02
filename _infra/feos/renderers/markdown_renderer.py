# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ContextPackage, EscalationPackage


class MarkdownRenderer:
    def __init__(self, renderer_id: str = "generic_markdown"):
        self.renderer_id = renderer_id

    def render(self, package: EscalationPackage, context: ContextPackage) -> str:
        lines = [
            "# External Reasoning Request",
            "",
            "## 1. Role",
            "You are an external reasoning model reviewing a FORGE Escalation Case.",
            "",
            "## 2. Task",
            "Analyze the evidence and provide verified, non-executing recommendations.",
            "",
            "## 3. Case Metadata",
            f"- Case ID: {package.case_id}",
            f"- Package ID: {package.id}",
            f"- Provider: {package.provider}",
            "",
        ]
        for section in context.sections:
            lines.extend([f"## {section.title}", section.content, ""])
        lines.extend([
            "## Required Response Format",
            "Return structured Markdown or YAML with: root_cause, recommendations, risks, assumptions, verification_plan.",
            "Do not claim execution was performed. Do not request secrets.",
            "",
        ])
        return "\n".join(lines)

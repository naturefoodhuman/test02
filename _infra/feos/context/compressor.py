# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ContextSection


class ContextCompressor:
    def compress_section(self, section: ContextSection, max_chars: int = 4000) -> ContextSection:
        if len(section.content) <= max_chars:
            return section
        section.content = section.content[:max_chars] + "\n...[truncated]"
        return section

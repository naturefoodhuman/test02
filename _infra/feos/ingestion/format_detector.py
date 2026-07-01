# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations


def detect_format(text: str) -> str:
    if "```yaml" in text or "```yml" in text:
        return "markdown_with_yaml"
    if text.strip().startswith("{"):
        return "json"
    return "markdown"

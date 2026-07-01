# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import re


def extract_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = "body"
    sections[current] = []
    for line in text.splitlines():
        m = re.match(r"^#{1,3}\s+(.+)$", line)
        if m:
            current = m.group(1).strip().lower().replace(" ", "_")
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}

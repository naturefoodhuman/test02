# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations


def extract_assumptions(parsed: dict) -> list[str]:
    sections = parsed.get("sections", {})
    out = []
    for key, value in sections.items():
        if "assumption" in key or ("recommendation" in key and "assumption" == "recommendation") or ("risk" in key and "assumption" == "risk"):
            out.extend([line.lstrip("- ").strip() for line in value.splitlines() if line.strip() and not line.strip().startswith("```") and not line.strip().startswith("+")])
    for block in parsed.get("yaml_blocks", []):
        value = block.get("assumptions") or block.get("assumption")
        if isinstance(value, list): out.extend(map(str, value))
        elif isinstance(value, str): out.append(value)
    return out

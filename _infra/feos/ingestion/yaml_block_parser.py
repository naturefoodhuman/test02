# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import re

import yaml


def extract_yaml_blocks(text: str) -> tuple[list[dict], list[str]]:
    warnings = []
    blocks = []
    for m in re.finditer(r"```ya?ml\n(.*?)\n```", text, flags=re.S | re.I):
        raw = m.group(1)
        try:
            parsed = yaml.safe_load(raw)
            if isinstance(parsed, dict):
                blocks.append(parsed)
        except Exception as exc:
            warnings.append(f"malformed yaml block: {exc}")
    return blocks, warnings

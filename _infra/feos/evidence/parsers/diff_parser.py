# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Git diff parser."""

from __future__ import annotations

import re


def parse_diff_paths(text: str) -> list[str]:
    paths = []
    for line in text.splitlines():
        match = re.match(r"\+\+\+ b/(.+)", line)
        if match:
            paths.append(match.group(1))
    return paths

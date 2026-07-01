# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Stack trace parser."""

from __future__ import annotations


def parse_stacktrace(text: str) -> dict:
    lines = [line for line in text.splitlines() if line.strip()]
    error_line = lines[-1] if lines else ""
    frames = [line.strip() for line in lines if line.lstrip().startswith("File ")]
    return {"error_line": error_line, "frame_count": len(frames), "frames": frames[:20]}

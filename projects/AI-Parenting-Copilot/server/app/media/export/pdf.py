# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 08:40:00

"""PDF export placeholder.

Real HTML->PDF renderer can be added later; P0 keeps a deterministic placeholder
so API/tests can mark PDF as unsupported instead of silently failing.
"""

from __future__ import annotations


def render_pdf_placeholder(markdown: str) -> bytes:
    return ("PDF export placeholder\n\n" + markdown).encode("utf-8")

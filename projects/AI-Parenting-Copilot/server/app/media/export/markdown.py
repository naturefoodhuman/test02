# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 08:40:00

"""Markdown export renderer."""

from __future__ import annotations


def render_markdown_summary(*, title: str, events: list[dict[str, object]]) -> str:
    lines = [f"# {title}", "", "## Events", ""]
    if not events:
        lines.append("No events in range.")
    for event in events:
        lines.append(f"- **{event.get('event_type', 'unknown')}**: {event.get('summary', '')}")
    lines.append("")
    return "\n".join(lines)

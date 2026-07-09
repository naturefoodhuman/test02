# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 06:40:00


"""Supplement reminder job."""

from __future__ import annotations


class SupplementReminderJob:
    name = "supplement"

    def __init__(self, todos: list[dict[str, object]] | None = None) -> None:
        self.todos = todos or []

    async def run(self) -> dict[str, object]:
        return {
            "kind": "supplement",
            "todos": self.todos,
            "alert_level": "blue" if self.todos else None,
        }

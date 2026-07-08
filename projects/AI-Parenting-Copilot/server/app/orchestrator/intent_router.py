# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 04:25:00


"""Intent routing for Orchestrator."""

from __future__ import annotations

import re


class IntentRouter:
    def route(self, text: str) -> str:
        lowered = text.lower()
        if any(keyword in lowered for keyword in ["配置", "config", "设置"]):
            return "config"
        if any(keyword in lowered for keyword in ["发烧", "体温", "咳嗽", "triage", "求助"]):
            return "triage"
        if any(keyword in lowered for keyword in ["确认告警", "ack", "alert"]):
            return "alert_ack"
        if re.search(r"(喂|奶|尿布|便便|体温|睡)", text):
            return "record"
        return "question"

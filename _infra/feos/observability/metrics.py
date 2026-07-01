# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import json
from pathlib import Path

from _infra.feos.storage import atomic_write_text


class MetricsStore:
    def __init__(self, metrics_dir: Path):
        self.metrics_dir = metrics_dir
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.counters_path = self.metrics_dir / "counters.json"
        self.events_path = self.metrics_dir / "events.jsonl"

    def increment(self, name: str, amount: int = 1) -> None:
        try:
            counters = json.loads(self.counters_path.read_text(encoding="utf-8")) if self.counters_path.exists() else {}
            counters[name] = counters.get(name, 0) + amount
            atomic_write_text(self.counters_path, json.dumps(counters, ensure_ascii=False, indent=2) + "\n")
        except Exception:
            pass

    def event(self, payload: dict) -> None:
        try:
            with self.events_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:
            pass

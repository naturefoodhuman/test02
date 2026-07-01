# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations


class KnowledgeOSAdapter:
    def __init__(self, sink=None):
        self.sink = sink

    def write_candidate(self, candidate):
        if self.sink and hasattr(self.sink, "write_candidate"):
            return self.sink.write_candidate(candidate)
        return None

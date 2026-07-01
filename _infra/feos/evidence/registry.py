# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Evidence collector registry."""

from __future__ import annotations

from _infra.feos.errors import FEOSError
from _infra.feos.ports.collectors import EvidenceCollectionRequest, EvidenceCollector


class CollectorRegistry:
    def __init__(self):
        self._collectors: dict[str, EvidenceCollector] = {}

    def register(self, collector: EvidenceCollector) -> None:
        if collector.collector_id in self._collectors:
            raise FEOSError(f"duplicate collector id: {collector.collector_id}")
        self._collectors[collector.collector_id] = collector

    def get(self, collector_id: str) -> EvidenceCollector:
        return self._collectors[collector_id]

    def enabled_collectors(self, request: EvidenceCollectionRequest, enabled_ids: list[str] | None = None) -> list[EvidenceCollector]:
        collectors = list(self._collectors.values())
        if enabled_ids is not None:
            allowed = set(enabled_ids)
            collectors = [collector for collector in collectors if collector.collector_id in allowed]
        return [collector for collector in collectors if collector.can_collect(request)]


def create_default_registry(root=None) -> CollectorRegistry:
    from pathlib import Path
    from .collectors import (
        ADRCollector, AgentPlanCollector, ArchitectureCollector, CodeCollector, ConfigCollector,
        DependencyCollector, DiffCollector, EnvironmentCollector, GitCollector, LogCollector,
        PreviousAttemptCollector, RuntimeCollector, StackTraceCollector, TestCollector, UserInputCollector,
    )

    root_path = Path(root) if root is not None else Path.cwd()
    registry = CollectorRegistry()
    for collector in [
        UserInputCollector(), PreviousAttemptCollector(), AgentPlanCollector(), GitCollector(root_path),
        DiffCollector(root_path), CodeCollector(root_path), StackTraceCollector(), LogCollector(root_path),
        RuntimeCollector(), TestCollector(), ConfigCollector(root_path), EnvironmentCollector(),
        DependencyCollector(root_path), ADRCollector(root_path), ArchitectureCollector(root_path),
    ]:
        registry.register(collector)
    return registry

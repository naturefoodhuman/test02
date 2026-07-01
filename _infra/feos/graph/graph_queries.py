# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Graph query helpers."""

from __future__ import annotations

from _infra.feos.models import CaseGraph, GraphNode


def nodes_by_type(graph: CaseGraph, node_type: str) -> list[GraphNode]:
    return [node for node in graph.nodes if node.type == node_type]

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Case graph model."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .base import FEOSModel


GRAPH_NODE_TYPES = {"case", "evidence", "fact", "hypothesis", "decision", "constraint", "action"}
GRAPH_EDGE_TYPES = {"supports", "refutes", "relates", "causes", "depends_on", "derived_from", "verifies"}


class GraphNode(FEOSModel):
    id: str
    type: str
    label: str
    ref_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(FEOSModel):
    source: str
    target: str
    type: str
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    data: dict[str, Any] = Field(default_factory=dict)


class CaseGraph(FEOSModel):
    id: str
    case_id: str
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    graph_hash: str | None = None

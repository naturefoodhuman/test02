# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-19 00:00:00
"""五层长期记忆（APC-T026）。

架构（ENGINEERING_DESIGN §5.9 / ARCHITECTURE_FINAL §6.5）：M1 硬事实 / M2 家庭偏好 /
M3 行为基线 / M4 短期上下文 / M5 纠错记忆。Orchestrator 经 ``MemoryInjector`` 一次性
聚合为 ``MemorySnapshot`` 注入健康类回答上下文（PRD §9）。
"""

from .domain import (
    Baseline,
    Correction,
    CorrectionStore,
    FamilyPrefs,
    HardFacts,
    MemorySnapshot,
    MemoryStore,
    ShortContext,
)
from .injector import MemoryInjector
from .rag_adapter import FakeRagStore, ForgeRagStore
from .store import SqlAlchemyMemoryStore

__all__ = [
    "Baseline",
    "Correction",
    "CorrectionStore",
    "FakeRagStore",
    "FamilyPrefs",
    "ForgeRagStore",
    "HardFacts",
    "MemoryInjector",
    "MemorySnapshot",
    "MemoryStore",
    "ShortContext",
    "SqlAlchemyMemoryStore",
]

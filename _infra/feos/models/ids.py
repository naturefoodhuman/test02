# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""FEOS ID generation utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Callable


Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_now_iso() -> str:
    return utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class FEOSIdGenerator:
    """Deterministic-friendly FEOS ID generator."""

    clock: Clock = utc_now
    counters: dict[str, int] = field(default_factory=dict)

    def next(self, prefix: str) -> str:
        now = self.clock()
        day = now.strftime("%Y_%m_%d")
        key = f"{prefix}_{day}"
        self.counters[key] = self.counters.get(key, 0) + 1
        return f"{prefix}_{day}_{self.counters[key]:03d}"

    def case_id(self) -> str:
        return self.next("case")

    def evidence_id(self, kind: str = "ev") -> str:
        return self.next(kind)

    def graph_id(self) -> str:
        return self.next("graph")

    def package_id(self) -> str:
        return self.next("pkg")

    def response_id(self) -> str:
        return self.next("resp")

    def verification_id(self) -> str:
        return self.next("ver")

    def plan_id(self) -> str:
        return self.next("plan")


_global_generator = FEOSIdGenerator()


def new_case_id() -> str:
    return _global_generator.case_id()

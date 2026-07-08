# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 02:50:00


"""Rule Engine kernel wrapper."""

from __future__ import annotations

from server.app.rule_engine.domain.models import RuleInput, RuleResult
from server.app.rule_engine.registry import RuleModule, RuleRegistry


class RuleEngine:
    """Small façade around RuleRegistry used by API/Copilots."""

    def __init__(self, registry: RuleRegistry | None = None) -> None:
        self.registry = registry or RuleRegistry()

    def register(self, module: RuleModule) -> None:
        self.registry.register(module)

    def evaluate(
        self,
        domain: str,
        payload: dict[str, object],
        context: dict[str, object] | None = None,
    ) -> RuleResult:
        return self.registry.evaluate(
            RuleInput(domain=domain, payload=dict(payload), context=dict(context or {}))
        )

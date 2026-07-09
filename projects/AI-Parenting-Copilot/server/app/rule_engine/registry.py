# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 02:50:00


"""Rule module registry."""

from __future__ import annotations

from typing import Protocol

from server.app.common.errors import ConflictError, NotFoundError
from server.app.rule_engine.domain.models import RuleInput, RuleResult


class RuleModule(Protocol):
    domain: str
    rule_version: str

    def evaluate(self, rule_input: RuleInput) -> RuleResult: ...


class RuleRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, RuleModule] = {}

    def register(self, module: RuleModule) -> None:
        if module.domain in self._modules:
            raise ConflictError(
                "Rule module already registered",
                evidence={"domain": module.domain},
            )
        self._modules[module.domain] = module

    def get(self, domain: str) -> RuleModule:
        module = self._modules.get(domain)
        if module is None:
            raise NotFoundError("Rule module not registered", evidence={"domain": domain})
        return module

    def evaluate(self, rule_input: RuleInput) -> RuleResult:
        return self.get(rule_input.domain).evaluate(rule_input)

    def domains(self) -> list[str]:
        return sorted(self._modules)

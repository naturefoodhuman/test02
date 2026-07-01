# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ContextPackage, EscalationCase, Evidence, Hypothesis
from _infra.feos.repositories import ContextRepository
from .compiler import ContextCompiler


class ContextService:
    def __init__(self, repository: ContextRepository, compiler: ContextCompiler | None = None):
        self.repository = repository
        self.compiler = compiler or ContextCompiler()

    def compile_and_save(self, case: EscalationCase, evidence: list[Evidence], hypotheses: list[Hypothesis] | None = None, budget: int = 24000) -> ContextPackage:
        package = self.compiler.compile(case, evidence, hypotheses=hypotheses, budget=budget)
        self.repository.put_yaml(case.id, package.id, package.to_dict())
        return package

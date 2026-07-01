# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import EscalationCase, Evidence, Hypothesis, ContextPackage
from _infra.feos.models.ids import FEOSIdGenerator
from .compressor import ContextCompressor
from .packer import ContextPacker
from .section_builder import SectionBuilder
from .selector import ContextSelector


class ContextCompiler:
    def __init__(self, id_generator: FEOSIdGenerator | None = None):
        self.ids = id_generator or FEOSIdGenerator()
        self.builder = SectionBuilder()
        self.selector = ContextSelector()
        self.compressor = ContextCompressor()
        self.packer = ContextPacker()

    def compile(self, case: EscalationCase, evidence: list[Evidence], hypotheses: list[Hypothesis] | None = None, budget: int = 24000) -> ContextPackage:
        selected, omitted = self.selector.select_evidence(evidence)
        sections = [
            self.builder.build_case_section(case),
            self.builder.build_evidence_section(selected),
            self.builder.build_hypothesis_section(hypotheses or []),
            self.builder.build_constraints_section(),
        ]
        sections = [self.compressor.compress_section(section) for section in sections]
        package, warnings = self.packer.pack(self.ids.next("ctxpkg"), case.id, sections, budget)
        package.metadata["omitted"] = omitted
        package.metadata["warnings"] = warnings
        return package

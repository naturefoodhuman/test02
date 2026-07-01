# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ContextPackage, EscalationPackage, Evidence
from _infra.feos.repositories import PackageRepository
from .builder import EscalationPackageBuilder


class EscalationPackageService:
    def __init__(self, repository: PackageRepository, builder: EscalationPackageBuilder | None = None):
        self.repository = repository
        self.builder = builder or EscalationPackageBuilder()

    def build_and_save(self, context: ContextPackage, evidence: list[Evidence] | None = None, gateway: str = "clipboard", provider: str = "chatgpt_web", renderer_profile: str = "generic_markdown") -> EscalationPackage:
        pkg, manifest = self.builder.build(context, evidence=evidence, gateway=gateway, provider=provider, renderer_profile=renderer_profile)
        self.repository.put_json(context.case_id, "package", pkg.to_dict())
        self.repository.put_json(context.case_id, "manifest", manifest)
        return pkg

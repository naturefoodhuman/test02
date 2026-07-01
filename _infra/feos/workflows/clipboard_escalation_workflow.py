# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.context import ContextService
from _infra.feos.evidence import EvidenceService, create_default_registry
from _infra.feos.gateways import ClipboardGateway
from _infra.feos.graph import CaseGraphService
from _infra.feos.models import EscalationPackage
from _infra.feos.package import EscalationPackageService
from _infra.feos.policy import PolicyEngine
from _infra.feos.ports.collectors import EvidenceCollectionRequest
from _infra.feos.renderers import create_default_renderer_registry
from _infra.feos.repositories import ContextRepository, GraphRepository, PackageRepository, TimelineRepository
from _infra.feos.storage import FEOSWorkspace


class ClipboardEscalationWorkflow:
    def __init__(self, workspace: FEOSWorkspace, root=None):
        self.workspace = workspace
        self.registry = create_default_registry(root)

    def collect(self, case, enabled_collectors: list[str] | None = None) -> list:
        service = EvidenceService(self.workspace, self.registry, TimelineRepository(self.workspace))
        request = EvidenceCollectionRequest(case_id=case.id, user_input=case.problem.user_goal)
        # Default Clipboard E2E export must be safe and minimal. Full collectors
        # can include canary config or sensitive local context and are invoked
        # explicitly by later evidence workflows, not by the basic export smoke.
        result = service.collect(request, enabled_collectors=enabled_collectors or ["user_input"])
        return result.evidence

    def build_graph(self, case_id: str, evidence: list):
        return CaseGraphService(GraphRepository(self.workspace)).build_and_save(case_id, evidence)

    def compile_context(self, case, evidence: list):
        return ContextService(ContextRepository(self.workspace)).compile_and_save(case, evidence)

    def build_package(self, context, evidence: list, provider: str = "chatgpt_web") -> EscalationPackage:
        return EscalationPackageService(PackageRepository(self.workspace)).build_and_save(context, evidence=evidence, provider=provider)

    def export_clipboard(self, package: EscalationPackage, context) -> dict:
        renderer = create_default_renderer_registry().get(package.renderer_profile)
        rendered = renderer.render(package, context)
        policy = PolicyEngine().check_export(rendered, gateway="clipboard", estimated_tokens=context.token_estimate)
        return ClipboardGateway(self.workspace).prepare(package, rendered, policy)

    def run_until_export(self, case, provider: str = "chatgpt_web") -> dict:
        evidence = self.collect(case)
        graph = self.build_graph(case.id, evidence)
        context = self.compile_context(case, evidence)
        package = self.build_package(context, evidence, provider=provider)
        export = self.export_clipboard(package, context)
        return {"evidence": evidence, "graph": graph, "context": context, "package": package, "export": export}

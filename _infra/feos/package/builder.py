# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ContextPackage, EscalationPackage, Evidence
from _infra.feos.models.ids import FEOSIdGenerator
from _infra.feos.storage import sha256_text
from .attachment_builder import allowed_attachment_refs
from .manifest import build_manifest
from .output_contract import default_output_contract


class EscalationPackageBuilder:
    def __init__(self, id_generator: FEOSIdGenerator | None = None):
        self.ids = id_generator or FEOSIdGenerator()

    def build(self, context: ContextPackage, evidence: list[Evidence] | None = None, gateway: str = "clipboard", provider: str = "chatgpt_web", renderer_profile: str = "generic_markdown") -> tuple[EscalationPackage, dict]:
        pkg = EscalationPackage(id=self.ids.package_id(), case_id=context.case_id, context_package_id=context.id, gateway=gateway, provider=provider, renderer_profile=renderer_profile)
        manifest = build_manifest(pkg, context)
        manifest["output_contract"] = default_output_contract()
        manifest["attachments"] = allowed_attachment_refs(evidence or [])
        pkg.manifest_ref = "package/manifest.json"
        pkg.content_hash = sha256_text(str(manifest))
        return pkg, manifest

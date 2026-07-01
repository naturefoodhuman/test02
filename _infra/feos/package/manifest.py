# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ContextPackage, EscalationPackage


def build_manifest(package: EscalationPackage, context: ContextPackage) -> dict:
    return {
        "package_id": package.id,
        "case_id": package.case_id,
        "context_package_id": context.id,
        "gateway": package.gateway,
        "provider": package.provider,
        "renderer_profile": package.renderer_profile,
        "token_estimate": context.token_estimate,
    }

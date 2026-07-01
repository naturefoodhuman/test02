# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from typing import Protocol

from _infra.feos.models import EscalationPackage, GatewayCapabilities


class EscalationGateway(Protocol):
    gateway_id: str
    capabilities: GatewayCapabilities

    def prepare(self, package: EscalationPackage, rendered_markdown: str, policy_result) -> dict: ...

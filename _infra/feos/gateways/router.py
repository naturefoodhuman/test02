# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.errors import FEOSError
from .registry import GatewayRegistry


class GatewayRouter:
    def __init__(self, registry: GatewayRegistry):
        self.registry = registry

    def select_gateway(self, requested_gateway: str | None = None):
        gateway = self.registry.get(requested_gateway or "clipboard")
        if not gateway.capabilities.enabled:
            raise FEOSError(f"gateway disabled: {gateway.gateway_id}")
        return gateway

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.errors import FEOSError
from _infra.feos.ports.gateways import EscalationGateway
from .api_gateway import APIGateway
from .browser_gateway import BrowserGateway
from .clipboard_gateway import ClipboardGateway
from .cloud_agent_gateway import CloudAgentGateway
from .mcp_gateway import MCPGateway


class GatewayRegistry:
    def __init__(self):
        self._gateways = {}

    def register(self, gateway: EscalationGateway) -> None:
        self._gateways[gateway.gateway_id] = gateway

    def get(self, gateway_id: str) -> EscalationGateway:
        if gateway_id not in self._gateways:
            raise FEOSError(f"unknown gateway: {gateway_id}")
        return self._gateways[gateway_id]


def create_default_gateway_registry(workspace=None) -> GatewayRegistry:
    registry = GatewayRegistry()
    registry.register(ClipboardGateway(workspace))
    registry.register(APIGateway())
    registry.register(MCPGateway())
    registry.register(BrowserGateway())
    registry.register(CloudAgentGateway())
    return registry

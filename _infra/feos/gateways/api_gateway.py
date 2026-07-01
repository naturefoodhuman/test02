# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.errors import FEOSError
from _infra.feos.models import GatewayCapabilities


class APIGateway:
    gateway_id = "api"

    def __init__(self):
        self.capabilities = GatewayCapabilities(gateway="api", enabled=False)

    def prepare(self, *args, **kwargs):
        raise FEOSError("gateway disabled: api")

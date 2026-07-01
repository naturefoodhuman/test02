# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""FEOS gateway layer."""

from .clipboard_gateway import ClipboardGateway
from .registry import GatewayRegistry, create_default_gateway_registry
from .router import GatewayRouter

__all__ = ["ClipboardGateway", "GatewayRegistry", "GatewayRouter", "create_default_gateway_registry"]

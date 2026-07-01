# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import pytest

from _infra.feos.errors import FEOSError
from _infra.feos.gateways import GatewayRouter, create_default_gateway_registry


def test_clipboard_selected_by_default_and_future_disabled():
    router = GatewayRouter(create_default_gateway_registry())
    assert router.select_gateway().gateway_id == "clipboard"
    with pytest.raises(FEOSError):
        router.select_gateway("api")
    with pytest.raises(FEOSError):
        router.select_gateway("mcp")

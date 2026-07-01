# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.errors import FEOSError
from _infra.feos.ports.renderers import Renderer
from .json_renderer import JSONRenderer
from .markdown_renderer import MarkdownRenderer
from .mcp_message_renderer import MCPMessageRenderer


class RendererRegistry:
    def __init__(self):
        self._renderers: dict[str, Renderer] = {}

    def register(self, renderer: Renderer) -> None:
        if renderer.renderer_id in self._renderers:
            raise FEOSError(f"duplicate renderer id: {renderer.renderer_id}")
        self._renderers[renderer.renderer_id] = renderer

    def get(self, renderer_id: str) -> Renderer:
        if renderer_id not in self._renderers:
            raise FEOSError(f"unknown renderer profile: {renderer_id}")
        return self._renderers[renderer_id]


def create_default_renderer_registry() -> RendererRegistry:
    registry = RendererRegistry()
    for rid in ["generic_markdown", "gpt_markdown_debug", "claude_markdown_architecture"]:
        registry.register(MarkdownRenderer(rid))
    registry.register(JSONRenderer())
    registry.register(MCPMessageRenderer())
    return registry

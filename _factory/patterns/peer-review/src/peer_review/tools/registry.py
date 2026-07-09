# 创建时间（北京时间）：2026-07-09 17:05:00
"""ToolRegistry: 工具注册表

管理工具的定义、查找、执行。
支持按名称过滤 (配合 ModelConfig.tools 使用)。
"""

from __future__ import annotations

import json
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ToolDefinition:
    """单个工具的定义"""
    name: str
    schema: dict[str, Any]          # OpenAI function schema
    handler: Callable[..., Any]     # 执行函数
    description: str = ""


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        schema: dict[str, Any],
        handler: Callable[..., Any],
        *,
        description: str = "",
    ) -> None:
        """注册一个工具

        Args:
            name: 工具名称 (需与 schema["name"] 一致)
            schema: OpenAI function calling 格式的 JSON Schema
            handler: 执行函数，参数与 schema.parameters 对应
            description: 工具描述 (可选，通常写在 schema 里)
        """
        self._tools[name] = ToolDefinition(
            name=name,
            schema=schema,
            handler=handler,
            description=description,
        )

    def unregister(self, name: str) -> None:
        """移除一个工具"""
        self._tools.pop(name, None)

    def get(self, name: str) -> ToolDefinition | None:
        """获取工具定义"""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """列出所有已注册的工具名称"""
        return list(self._tools.keys())

    def get_schemas(self, names: list[str] | None = None) -> list[dict[str, Any]]:
        """返回 OpenAI tools 格式的 JSON Schema 列表

        Args:
            names: 如果指定，只返回这些名称的工具 schema
        """
        if names is not None:
            return [
                {"type": "function", "function": self._tools[n].schema}
                for n in names
                if n in self._tools
            ]
        return [
            {"type": "function", "function": t.schema}
            for t in self._tools.values()
        ]

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        """执行工具，返回字符串结果

        Args:
            name: 工具名称
            arguments: 解析后的参数 dict

        Returns:
            JSON 字符串或纯字符串 (会被回填到 tool message)
        """
        if name not in self._tools:
            return json.dumps({"error": f"未知工具: {name}", "available": self.list_tools()})

        tool_def = self._tools[name]
        try:
            result = tool_def.handler(**arguments)
            if isinstance(result, (dict, list)):
                return json.dumps(result, ensure_ascii=False, default=str)
            return str(result)
        except TypeError as e:
            # 参数不匹配
            return json.dumps({"error": f"参数错误: {e}", "tool": name})
        except Exception as e:
            # 执行异常
            return json.dumps({
                "error": str(e),
                "tool": name,
                "traceback": traceback.format_exc()[-500:],  # 截断
            })

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
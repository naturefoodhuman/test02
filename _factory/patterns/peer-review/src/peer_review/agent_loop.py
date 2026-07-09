# 创建时间（北京时间）：2026-07-09 17:05:00
"""Agent Loop 核心循环

实现 ReAct 风格的 tool-use agent：
1. 调用 LLM (带 tools)
2. 检测 tool_calls
3. 执行工具 → 回填结果
4. 循环直到无 tool_calls 或达到 max_turns
"""

from __future__ import annotations

import json
from typing import Any, Callable, TYPE_CHECKING

from peer_review.llm_client import LLMResponse, ToolCall, chat

if TYPE_CHECKING:
    from peer_review.config.schemas import ModelConfig
    from peer_review.tools.registry import ToolRegistry


def run_agent_loop(
    model_cfg: "ModelConfig",
    messages: list[dict[str, Any]],
    tool_registry: "ToolRegistry",
    *,
    max_turns: int = 10,
    privacy_context: dict[str, Any] | None = None,
    on_tool_call: Callable[[ToolCall], None] | None = None,
    on_tool_result: Callable[[str, str], None] | None = None,
) -> LLMResponse:
    """Agent Loop 核心循环

    Args:
        model_cfg: 模型配置
        messages: 初始对话消息 (会被原地修改，建议传入副本)
        tool_registry: 工具注册表
        max_turns: 最大循环轮次
        privacy_context: 隐私校验上下文
        on_tool_call: 每次工具调用前的回调 (用于日志/UI)
        on_tool_result: 每次工具执行后的回调 (name, result_str)

    Returns:
        最终的 LLMResponse (最后一个无 tool_calls 的响应)
    """
    tools_schema = tool_registry.get_schemas()

    if not tools_schema:
        # 没有注册任何工具，直接单次调用
        return chat(model_cfg, messages, privacy_context=privacy_context)

    # 使用副本避免修改原始 messages
    history = list(messages)

    for turn in range(max_turns):
        resp = chat(
            model_cfg,
            history,
            tools=tools_schema,
            privacy_context=privacy_context,
        )

        # 如果响应被阻断 (隐私/错误)，直接返回
        if resp.blocked or resp.error:
            return resp

        # 没有 tool_calls → 返回最终答案
        if not resp.tool_calls:
            return resp

        # ── 有 tool_calls → 执行工具 ──
        print(f"🔧 [Turn {turn + 1}] 模型请求 {len(resp.tool_calls)} 个工具调用")

        # 1. 把 assistant 的 tool_calls 消息追加到历史
        assistant_msg: dict[str, Any] = {
            "role": "assistant",
            "content": resp.content or None,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": tc.raw_arguments or json.dumps(tc.arguments, ensure_ascii=False),
                    },
                }
                for tc in resp.tool_calls
            ],
        }
        history.append(assistant_msg)

        # 2. 逐个执行工具调用
        for tc in resp.tool_calls:
            # 回调: 工具调用前
            if on_tool_call:
                on_tool_call(tc)

            print(f"  📞 调用工具: {tc.name}({json.dumps(tc.arguments, ensure_ascii=False)[:100]})")

            # 执行
            result_str = tool_registry.execute(tc.name, tc.arguments)

            print(f"  ✅ 结果: {result_str[:200]}")

            # 回调: 工具结果
            if on_tool_result:
                on_tool_result(tc.name, result_str)

            # 3. 把 tool result 追加到历史
            history.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_str,
            })

    # ── 超限降级 ──
    print(f"⚠️ Agent Loop 达到最大轮次 {max_turns}")
    return LLMResponse(
        content=f"[Agent Loop 达到最大轮次 {max_turns}，已停止循环]",
        model=model_cfg.model_id,
        error="max_turns_exceeded",
        finish_reason="length",
    )
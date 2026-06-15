# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 02:05:00 CST
"""LangGraph ReviewState 定义

所有 Agent 数据显式管理，无隐式状态。
并行节点写入的字段使用 Annotated + reducer，保证 HUB-SPOKE 收集正常。
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class ReviewState(TypedDict, total=False):
    """HUB-SPOKE 评审图状态"""

    case_context: str              # 案件上下文（原始输入）
    primary_analysis: str          # 主专家分析结论
    reviewer_opinions: Annotated[list[str], operator.add]   # 各评审独立意见（HUB-SPOKE 收集）
    reviewer_roles: Annotated[list[str], operator.add]       # 对应角色标签
    consensus: str                 # 最终汇总结论
    divergence_score: float        # 评审间分歧度（0-1）
    requires_human: bool           # 是否触发人工仲裁
    model_plan_id: str             # 本次使用的方案 ID（用于对比记录）
    models_used: Annotated[dict[str, str], operator.or_]   # 各节点实际使用的模型
    iron_gate_triggered: bool      # 铁闸是否触发
    iron_gate_reason: str          # 铁闸触发原因
    privacy_preview: dict[str, str]  # 出境数据预览（人工确认用）

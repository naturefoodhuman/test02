# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 01:25:00 CST
"""Peer-Review 平台层模块

包含 LangGraph 迁移后需要的平台级组件：
- RoutingPlanEngine: B 文件驱动的节点路由
- DataPrivacyGate: 策略文件驱动的数据出境门控
- MemoryStore: 跨会话记忆 + 方案对比记录
- KnowledgeHub: 知识统一接口
- DecisionEngine: 分层决策引擎
"""

from __future__ import annotations

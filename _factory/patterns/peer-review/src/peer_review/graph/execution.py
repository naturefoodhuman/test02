# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-21 03:00:00
"""评审引擎执行入口

封装 LangGraph 图的构建、状态管理与执行流程。
支持真实 LLM 调用（MTPLX / Ollama 等），完整 HUB-SPOKE 评审。

v1.2.1 更新：
- 修复函数签名，支持 project_root, data_fields, privacy_approved 等参数 (解决 Benchmark 报错)
- 对齐 SSOT 规范，支持按需加载与隐私校验上下文
"""

from __future__ import annotations

import time
import uuid
from typing import Any
from pathlib import Path

from peer_review.graph.review_graph import build_review_graph
from peer_review.platform.knowledge_hub import KnowledgeHub
from peer_review.platform.routing_plan_engine import RoutingPlanEngine
from peer_review.platform.memory_store import MemoryStore

def run_langgraph_review(
    query: str,
    project_root: Path | None = None,
    plan_id: str | None = None,
    data_fields: dict[str, Any] | None = None,
    privacy_endpoint: str | None = None,
    privacy_approved: bool | None = None,
    use_live: bool = True,
    root: Path | None = None, # 兼容旧参数名
) -> dict[str, Any]:
    """执行一次完整的评审流程（真实 LangGraph + 真实 LLM）

    Args:
        query: 案件上下文（支持字符串）
        project_root: 项目根目录
        plan_id: 指定路由方案 ID
        data_fields: 隐私校验原始字段
        privacy_endpoint: 隐私目标端点
        privacy_approved: 是否已人工授权隐私出境
        use_live: 是否使用实时进度展示
        root: 兼容性参数名 (同 project_root)
    """
    # 统一根目录参数
    effective_root = project_root or root or Path(".")
    
    # 1. 初始化平台组件
    routing_engine = RoutingPlanEngine(project_root=effective_root)
    knowledge_hub = KnowledgeHub(
        knowledge_root=effective_root / "_factory" / "experts",
        skills_root=effective_root / "_factory" / "skills"
    )

    # 临时切换方案
    if plan_id:
        routing_engine.set_active_plan(plan_id)
    
    active_plan = routing_engine.config.routing.active_plan

    # 2. 构建 LangGraph
    graph = build_review_graph(routing_engine, knowledge_hub)

    # 3. 准备初始状态
    initial_state = {
        "case_context": query,
        "reviewer_opinions": [],
        "reviewer_roles": [],
        "consensus": "",
        "final_decision": "",
        "requires_human": False,
        "iron_gate_triggered": False,
        "run_id": f"run-{uuid.uuid4().hex[:12]}",
        "model_plan_id": active_plan,
        "data_fields": data_fields,
        "privacy_endpoint": privacy_endpoint,
        "privacy_approved": privacy_approved,
        "models_used": {},
        "start_time": time.time(),
    }

    # 4. 执行
    thread_id = f"review-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        print(f"🚀 启动 LangGraph 评审 (方案={active_plan}, 线程={thread_id}) ...")
        # 实际执行
        final_state = graph.invoke(initial_state, config=config)

        # 5. 提取结果
        final_decision = (
            final_state.get("consensus")
            or final_state.get("primary_analysis")
            or "[无输出]"
        )
        divergence = final_state.get("divergence_score", 0.0)
        models_used = final_state.get("models_used", {})
        
        duration = time.time() - initial_state["start_time"]

        return {
            "final_decision": final_decision,
            "divergence_score": divergence,
            "run_id": final_state.get("run_id", thread_id),
            "models_used": models_used,
            "primary_analysis": final_state.get("primary_analysis", ""),
            "reviewer_opinions": final_state.get("reviewer_opinions", []),
            "thread_id": thread_id,
            "total_time": duration,
            "iron_gate_triggered": final_state.get("iron_gate_triggered", False),
            "iron_gate_reason": final_state.get("iron_gate_reason", ""),
            "requires_human": final_state.get("requires_human", False),
            "consensus": final_state.get("consensus", ""),
        }

    except Exception as e:
        print(f"❌ LangGraph 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "final_decision": f"[错误] {str(e)}",
            "divergence_score": 1.0,
            "error": str(e),
            "thread_id": thread_id
        }

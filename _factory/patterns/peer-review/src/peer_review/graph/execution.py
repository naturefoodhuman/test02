# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-16 12:10:00 CST
"""评审引擎执行入口

封装 LangGraph 图的构建、状态管理与执行流程。
支持真实 LLM 调用（MTPLX / Ollama 等），完整 HUB-SPOKE 评审。
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
    case_context: dict[str, Any],
    plan_id: str | None = None,
    use_live: bool = True,
    root: Path = Path("."),
) -> dict[str, Any]:
    """执行一次完整的评审流程（真实 LangGraph + 真实 LLM）

    Args:
        case_context: 案件上下文（ID, 内容等）。支持 str 或 dict（含 "input" 或 "content"）
        plan_id: 指定路由方案 ID（如果不指定则使用当前激活方案）
        use_live: 是否使用 Rich Live Display 展示进度（当前 evaluator 传 False）
        root: 项目根目录
    """
    # 1. 初始化平台组件（强制使用指定 root 保证 config 正确加载）
    routing_engine = RoutingPlanEngine(project_root=root)
    knowledge_hub = KnowledgeHub(
        knowledge_root=root / "_factory" / "experts",
        skills_root=root / "_factory" / "skills"
    )

    # 如果指定了 plan_id，则临时切换激活方案（mtplx-hybrid 等）
    if plan_id:
        routing_engine.set_active_plan(plan_id)

    # 2. 构建 LangGraph（HUB-SPOKE 结构）
    graph = build_review_graph(routing_engine, knowledge_hub)

    # 3. 规范化 case_context（支持 gold_dataset 的 "input" 字段）
    if isinstance(case_context, str):
        normalized_context = case_context
    else:
        normalized_context = (
            case_context.get("content")
            or case_context.get("input")
            or str(case_context)
        )
    case_id = (
        case_context.get("case_id")
        or case_context.get("id")
        or f"eval-{uuid.uuid4().hex[:8]}"
    )

    # 4. 准备初始状态（符合 ReviewState）
    initial_state = {
        "case_context": normalized_context,
        "reviewer_opinions": [],
        "reviewer_roles": [],
        "consensus": "",
        "final_decision": "",  # 兼容旧调用方
        "requires_human": False,
        "iron_gate_triggered": False,
        "run_id": f"run-{uuid.uuid4().hex[:12]}",
        "model_plan_id": routing_engine.get_plan_id_for_node("primary_expert") or plan_id or "default",
        "models_used": {},
        "start_time": time.time(),
    }

    # 5. 真实执行 LangGraph（使用 invoke 驱动完整流程，真实调用 LLM）
    thread_id = f"eval-{case_id}-{int(time.time())}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        print(f"🚀 启动真实 LangGraph 评审 (plan={plan_id or 'active'}, case={case_id}) ...")
        final_state = graph.invoke(initial_state, config=config)

        # 6. 提取结果（真实 LLM 输出）
        final_decision = (
            final_state.get("consensus")
            or final_state.get("primary_analysis")
            or final_state.get("final_decision")
            or "[无共识输出]"
        )
        divergence = final_state.get("divergence_score", 0.0)
        models_used = final_state.get("models_used", {})
        run_id = final_state.get("run_id", thread_id)

        start_ts = final_state.get("start_time", time.time())
        duration = max(0.1, time.time() - start_ts)  # 避免 0.0 导致 TPS 异常

        print(f"✅ LangGraph 评审完成 | plan={plan_id or 'active'} | div={divergence:.2f} | 耗时 {duration:.1f}s")
        if models_used:
            print(f"   使用模型: {models_used}")

        return {
            "final_decision": final_decision,
            "divergence_score": divergence,
            "run_id": run_id,
            "models_used": models_used,
            "primary_analysis": final_state.get("primary_analysis", ""),
            "reviewer_opinions": final_state.get("reviewer_opinions", []),
            "thread_id": thread_id,
            "total_time": duration,
        }

    except Exception as e:
        print(f"❌ LangGraph 真实执行失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "final_decision": f"[执行错误] {str(e)}",
            "divergence_score": 1.0,
            "run_id": f"error-{uuid.uuid4().hex[:8]}",
            "error": str(e),
        }

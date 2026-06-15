# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 11:00:00 CST
"""Memory 记录节点实现

职责：
- 在评审结束前，将运行元数据持久化到 MemoryStore
- 计算单次运行的耗时与预估成本
- 生成案件哈希，以便后续跨方案对比
"""

from __future__ import annotations

import time
import hashlib
from pathlib import Path
from typing import Any

from peer_review.graph.state import ReviewState
from peer_review.platform.memory_store import MemoryStore, ModelRunRecord
from peer_review.platform.routing_plan_engine import RoutingPlanEngine
from rich.console import Console

console = Console()


def make_record_run_node(routing_engine: RoutingPlanEngine):
    """创建记录运行结果的节点函数"""

    def record_run_node(state: ReviewState) -> ReviewState:
        # 1. 初始化 MemoryStore
        # 路径固定在 runtime/memory.db
        mem_store = MemoryStore(Path("runtime/memory.db"))

        # 2. 计算运行指标
        start_time = state.get("start_time")
        if start_time is None:
            console.print("[yellow]⚠️  未发现 start_time，无法记录耗时[/yellow]")
            return state

        end_time = time.time()
        duration = int(end_time - start_time)

        # 3. 估算成本 (基于 A 文件的 estimated_cost)
        total_cost = 0.0
        models_used = state.get("models_used", {})
        for node_name, model_id in models_used.items():
            model_cfg = routing_engine.config.models.models.get(model_id)
            if model_cfg and hasattr(model_cfg, "estimated_cost"):
                # 简单处理: 假设 estimated_cost 格式为 "$0.002/1k tokens"
                cost_str = model_cfg.estimated_cost or "0"
                try:
                    # 提取数字部分
                    val = cost_str.replace("$", "").split("/")[0]
                    total_cost += float(val) * 10 # 粗略估算单次调用 10k tokens
                except Exception:
                    pass

        # 4. 生成案件哈希
        case_text = state.get("case_context", "")
        case_hash = hashlib.sha256(case_text.encode()).hexdigest()[:16]

        # 5. 创建记录
        import random
        record = ModelRunRecord(
            run_id=f"run_{int(end_time)}_{random.randint(1000, 9999)}",
            case_hash=case_hash,
            plan_id=state.get("model_plan_id", "unknown"),
            models_used=models_used,
            total_time_seconds=duration,
            total_cost_usd=total_cost,
            divergence_score=state.get("divergence_score", 0.0),
            created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        )


        try:
            mem_store.record_run(record)
            console.print(f"[dim]📝 已记录运行结果至 MemoryStore (耗时: {duration}s, 成本: ${total_cost:.4f})[/dim]")
        except Exception as e:
            console.print(f"[red]❌ 记录运行结果失败: {e}[/red]")

        return state

    return record_run_node

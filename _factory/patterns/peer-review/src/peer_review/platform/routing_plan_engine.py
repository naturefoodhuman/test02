# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 01:30:00 CST
"""RoutingPlanEngine: B 文件驱动的节点路由引擎

职责：
- 加载 A 文件 (models.yaml) 与 B 文件 (routing_plans.yaml)
- 启动时交叉验证模型一致性
- 根据 active_plan 为每个节点返回模型配置
- 支持方案菜单展示、GPU 内存预检、并行安全验证
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from peer_review.config import ConfigurationError, load_all_configs
from peer_review.config.schemas import (
    AppConfig,
    ModelConfig,
    PlanConfig,
)


@dataclass
class PlanSummary:
    """方案菜单展示条目"""

    plan_id: str
    description: str
    estimated_time: str
    estimated_cost: str
    memory_safe: bool
    is_active: bool
    notes: str = ""


@dataclass
class MemorySafetyResult:
    """并行内存安全检查结果"""

    is_safe: bool
    estimated_gb: float
    message: str


class RoutingPlanEngine:
    """路由方案引擎"""

    def __init__(self, project_root: Path | None = None):
        self._project_root = project_root
        self.config: AppConfig = load_all_configs(project_root) if project_root else load_all_configs()

    def get_active_plan(self) -> PlanConfig:
        """获取当前激活方案"""
        return self.config.get_active_plan()

    def get_model_for_node(self, node_name: str) -> ModelConfig:
        """根据激活方案返回指定节点的模型配置"""
        return self.config.get_model_for_node(node_name)

    def list_plans_summary(self, available_mem_gb: float = 64.0) -> list[PlanSummary]:
        """生成方案选择菜单（含内存安全提示）"""
        summaries: list[PlanSummary] = []
        for plan_id, plan in self.config.routing.plans.items():
            if not plan.enabled:
                continue
            mem_check = self.check_parallel_memory_safety(plan_id, available_mem_gb)
            summaries.append(
                PlanSummary(
                    plan_id=plan_id,
                    description=plan.description,
                    estimated_time=plan.estimated_total_time,
                    estimated_cost=plan.estimated_cost,
                    memory_safe=mem_check.is_safe,
                    is_active=(plan_id == self.config.routing.active_plan),
                    notes=plan.notes or "",
                )
            )
        return summaries

    def check_parallel_memory_safety(
        self, plan_id: str, available_mem_gb: float = 64.0
    ) -> MemorySafetyResult:
        """检查并行执行时本地模型内存是否安全

        保守估计：所有并行节点中的 local 模型显存求和 * 1.15 + 8GB 系统保留
        """
        plan = self.config.routing.plans.get(plan_id)
        if plan is None:
            return MemorySafetyResult(
                is_safe=False, estimated_gb=0.0, message=f"方案 '{plan_id}' 不存在"
            )

        total_mem = 0.0
        for node_name, node_cfg in plan.nodes.items():
            if node_cfg.execution.value != "parallel":
                continue
            model_cfg = self.config.models.models.get(node_cfg.model)
            if model_cfg is None:
                continue
            if model_cfg.type.value == "local":
                total_mem += model_cfg.memory_required_gb

        total_mem_with_buffer = total_mem * 1.15 + 8.0
        if total_mem_with_buffer > available_mem_gb:
            return MemorySafetyResult(
                is_safe=False,
                estimated_gb=total_mem_with_buffer,
                message=(
                    f"并行内存需求 {total_mem_with_buffer:.1f}GB 超出 {available_mem_gb}GB，"
                    "将自动降级为信息屏蔽顺序模式"
                ),
            )
        return MemorySafetyResult(
            is_safe=True,
            estimated_gb=total_mem_with_buffer,
            message=f"并行内存预估 {total_mem_with_buffer:.1f}GB，安全",
        )

    def get_plan_id_for_node(self, node_name: str) -> str:
        """返回当前激活方案 ID（用于记录）"""
        return self.config.routing.active_plan

    def get_available_plans(self) -> list[str]:
        """返回所有启用的方案 ID 列表（兼容 evaluator 调用）"""
        return [
            plan_id
            for plan_id, plan in self.config.routing.plans.items()
            if plan.enabled
        ]

    def set_active_plan(self, plan_id: str) -> None:
        """临时切换激活方案（用于 eval 指定 --plans）"""
        if plan_id not in self.config.routing.plans:
            raise ValueError(f"方案 '{plan_id}' 不存在。可用方案: {self.get_available_plans()}")
        if not self.config.routing.plans[plan_id].enabled:
            raise ValueError(f"方案 '{plan_id}' 未启用")
        self.config.routing.active_plan = plan_id
        # 强制重新加载以确保一致性（简单实现）
        # 注意：生产环境建议使用不可变配置，这里为 eval 兼容
        print(f"✅ 已切换激活方案为: {plan_id}")

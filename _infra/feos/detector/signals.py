# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Detector input signals."""

from __future__ import annotations

from pydantic import Field

from _infra.feos.models.base import FEOSModel


class ExecutionFailureSignals(FEOSModel):
    repeated_failure_count: int = Field(0, ge=0)
    same_error_repeated: bool = False
    error_stability: float = Field(0.0, ge=0.0, le=1.0)
    failed_tests: int = Field(0, ge=0)


class AgentBehaviorSignals(FEOSModel):
    uncertainty: float = Field(0.0, ge=0.0, le=1.0)
    repeated_plan: bool = False
    tool_call_loop: bool = False
    declares_no_new_strategy: bool = False


class ContextHealthSignals(FEOSModel):
    context_pollution: float = Field(0.0, ge=0.0, le=1.0)
    context_window_exceeded: bool = False
    unresolved_assumption_count: int = Field(0, ge=0)


class TaskMetadataSignals(FEOSModel):
    task_complexity: float = Field(0.0, ge=0.0, le=1.0)
    missing_knowledge: float = Field(0.0, ge=0.0, le=1.0)
    user_priority: float = Field(0.0, ge=0.0, le=1.0)
    security_sensitive: bool = False
    architecture_decision_deadlock: bool = False


class DetectorSignals(FEOSModel):
    execution: ExecutionFailureSignals = Field(default_factory=ExecutionFailureSignals)
    agent: AgentBehaviorSignals = Field(default_factory=AgentBehaviorSignals)
    context: ContextHealthSignals = Field(default_factory=ContextHealthSignals)
    task: TaskMetadataSignals = Field(default_factory=TaskMetadataSignals)
    title: str = "Detected escalation candidate"
    user_goal: str = "Resolve local agent failure or uncertainty"

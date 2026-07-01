# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import pytest

from _infra.feos.errors import FEOSPolicyError
from _infra.feos.execution import ExecutionTracker, OutcomeEvaluator, approve_plan
from _infra.feos.models import ExecutionPlan, ExecutionStep


def test_approval_tracking_outcome():
    plan = ExecutionPlan(id="plan", case_id="case", verification_id="ver", steps=[ExecutionStep(id="s1", description="do")])
    with pytest.raises(FEOSPolicyError):
        ExecutionTracker().mark_step_completed(plan, "s1")
    plan = approve_plan(plan)
    assert ExecutionTracker().mark_step_completed(plan, "s1").steps[0].status == "completed"
    outcome = OutcomeEvaluator().record("case", "resolved", "fixed", plan_id="plan")
    assert outcome.status == "resolved"

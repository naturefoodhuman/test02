# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-13 16:35:00 CST
"""Peer-Review 专家评审引擎测试套件。

覆盖：专家加载、JSON解析、共识引擎、完整流程（LLM不可用时降级）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# ── 路径设置 ──
REPO_ROOT = Path(__file__).resolve().parents[4]  # /home/user/test02
PR_SRC = REPO_ROOT / "_factory" / "patterns" / "peer-review" / "src"
if str(PR_SRC) not in sys.path:
    sys.path.insert(0, str(PR_SRC))
DC_SRC = REPO_ROOT / "projects" / "debt-collection" / "src"
if str(DC_SRC) not in sys.path:
    sys.path.insert(0, str(DC_SRC))

import pytest

from peer_review.orchestrator import (
    Expert, ReviewDimension, ReviewResult, ConsensusReport,
    PeerReviewOrchestrator, _extract_json, _parse_review_result,
    build_case_context, _make_expert,
)


# ── 专家定义测试 ──

class TestExpert:
    """测试专家配置。"""

    def test_build_prompt(self):
        e = _make_expert()
        prompt, system = e.build_review_prompt(
            case_context="张三欠50000元，有借条。",
            primary_output="建议协商，发律师函。",
            dimension=ReviewDimension.RISK,
        )
        assert "张三" in prompt
        assert "协商" in prompt
        assert "risk" in prompt
        assert "JSON" in prompt

    def test_build_prompt_with_knowledge(self):
        e = _make_expert(knowledge="民间借贷诉讼时效为3年。")
        prompt, _ = e.build_review_prompt("案件", "方案", ReviewDimension.RISK)
        assert "民间借贷" in prompt

    def test_all_dimensions(self):
        e = _make_expert(dims=list(ReviewDimension))
        for dim in ReviewDimension:
            prompt, _ = e.build_review_prompt("案件", "方案", dim)
            assert dim.value in prompt

    def test_discover_experts(self):
        from peer_review.orchestrator import discover_experts, load_expert
        experts = discover_experts(REPO_ROOT / "_factory" / "experts")
        assert "risk-assessor" in experts
        assert "compliance-auditor" in experts
        assert "execution-strategist" in experts
        assert "debt-lawyer" in experts

    def test_load_risk_assessor(self):
        from peer_review.orchestrator import load_expert
        expert = load_expert("risk-assessor", REPO_ROOT / "_factory" / "experts")
        assert expert.id == "risk-assessor"
        assert "risk" in [d.value for d in expert.review_dimensions]
        assert expert.weight == 0.8

    def test_load_compliance_auditor(self):
        from peer_review.orchestrator import load_expert
        expert = load_expert("compliance-auditor", REPO_ROOT / "_factory" / "experts")
        assert expert.id == "compliance-auditor"
        assert "compliance" in [d.value for d in expert.review_dimensions]
        assert expert.weight == 0.9

    def test_load_execution_strategist(self):
        from peer_review.orchestrator import load_expert
        expert = load_expert("execution-strategist", REPO_ROOT / "_factory" / "experts")
        assert expert.id == "execution-strategist"
        assert "execution_strategy" in [d.value for d in expert.review_dimensions]
        assert expert.weight == 0.7


# ── JSON 解析测试 ──

class TestJSONExtraction:
    def test_extract_json_from_code_block(self):
        text = '```json\n{"score": 0.8, "issues": ["风险高"]}\n```'
        result = _extract_json(text)
        assert result is not None
        data = json.loads(result)
        assert data["score"] == 0.8

    def test_extract_json_from_plain_text(self):
        text = '评审结果：{"score": 0.6, "agreement": "部分同意"}'
        result = _extract_json(text)
        assert result is not None
        data = json.loads(result)
        assert data["agreement"] == "部分同意"

    def test_extract_json_no_json(self):
        assert _extract_json("这段文字没有JSON") is None

    def test_parse_review_result_valid_json(self):
        expert = _make_expert()
        response = '''```json
{
  "score": 0.7,
  "issues": ["证据不足", "时效临近"],
  "recommendations": ["补充借条", "尽快起诉"],
  "agreement": "部分同意",
  "dissenting_reason": "证据链不够完整",
  "confidence": 0.8
}
```'''
        result = _parse_review_result(expert, ReviewDimension.RISK, response)
        assert result.score == 0.7
        assert len(result.issues) == 2
        assert "证据不足" in result.issues
        assert result.agreement == "部分同意"
        assert result.confidence == 0.8
        assert "证据链不够完整" in result.dissenting_reason

    def test_parse_review_result_invalid_json(self):
        expert = _make_expert()
        result = _parse_review_result(expert, ReviewDimension.RISK, "这不是JSON格式的回复")
        assert result.score == 0.5
        assert len(result.recommendations) == 1


# ── 共识引擎测试 ──

class TestConsensusEngine:
    def test_all_agree(self):
        primary = _make_expert("primary", "主专家")
        reviewer = _make_expert("reviewer", "评审专家")
        orch = PeerReviewOrchestrator(primary_expert=primary, reviewers=[reviewer])

        reviews = [
            ReviewResult(expert_id="risk", expert_name="风险专家", dimension=ReviewDimension.RISK,
                        score=0.8, agreement="同意", recommendations=["建议1"], confidence=0.9),
            ReviewResult(expert_id="comp", expert_name="合规专家", dimension=ReviewDimension.COMPLIANCE,
                        score=0.7, agreement="同意", recommendations=["建议2"], confidence=0.8),
        ]

        consensus = orch._build_consensus("主方案", reviews)
        assert consensus.consensus_score == pytest.approx(0.76, abs=0.02)
        assert consensus.agreement_level == "一致同意"
        assert len(consensus.final_recommendations) == 2
        assert len(consensus.dissenting_notes) == 0

    def test_with_dissent(self):
        primary = _make_expert("primary", "主专家")
        reviewer = _make_expert("reviewer", "评审专家")
        orch = PeerReviewOrchestrator(primary_expert=primary, reviewers=[reviewer])

        reviews = [
            ReviewResult(expert_id="risk", expert_name="风险专家", dimension=ReviewDimension.RISK,
                        score=0.8, agreement="同意", confidence=0.9),
            ReviewResult(expert_id="comp", expert_name="合规专家", dimension=ReviewDimension.COMPLIANCE,
                        score=0.3, agreement="否", dissenting_reason="存在违法风险", confidence=0.7),
        ]

        consensus = orch._build_consensus("主方案", reviews)
        assert consensus.agreement_level == "分歧较大"
        assert len(consensus.dissenting_notes) == 1
        assert "违法风险" in consensus.dissenting_notes[0]

    def test_no_reviews(self):
        primary = _make_expert("primary", "主专家")
        orch = PeerReviewOrchestrator(primary_expert=primary, reviewers=[])
        consensus = orch._build_consensus("主方案", [])
        assert consensus.consensus_score == 0.0
        assert consensus.agreement_level == "无评审"


# ── 完整流程测试（LLM不可用时降级）──

class TestEndToEnd:
    def test_llm_failure_graceful(self):
        """当 LLM 不可用时，orchestrator 应优雅降级。"""
        primary = _make_expert("primary", "主专家")
        reviewer = _make_expert("reviewer", "评审专家")
        orch = PeerReviewOrchestrator(
            primary_expert=primary,
            reviewers=[reviewer],
            base_url="http://localhost:9999/v1",  # 不存在的端口
        )
        report = orch.run_review("张三欠50000元")
        assert "模型不可用" in report.agreement_level or "⚠️" in report.primary_output


# ── 案件上下文组装测试 ──

class TestCaseContext:
    def test_build_with_debt_model(self):
        from debt.models import Debt, DebtNature, DebtStage, Intel, IntelCredibility
        debt = Debt(
            id=1, debtor_name="张三", amount=50000, nature=DebtNature.PRIVATE_LOAN,
            debtor_region="杭州", lend_date="2024-01-01", due_date="2024-07-01",
            evidence=["借条", "转账记录"], stage=DebtStage.NEGOTIATION,
        )
        intels = [
            Intel(debt_id=1, content="债务人当选村支书", source="朋友",
                  credibility=IntelCredibility.MEDIUM, created_at="2026-05-01"),
        ]
        ctx = build_case_context(debt, intels)
        assert "张三" in ctx
        assert "50000" in ctx
        assert "村支书" in ctx
        assert "借条" in ctx

# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 03:00:00 CST
"""debt review 命令集成测试（LangGraph + DataPrivacyGate + MemoryStore）"""
from __future__ import annotations

from pathlib import Path

import pytest

from debt.cli import _estimate_cost, _extract_privacy_fields, _plan_uses_api
from debt.models import Debt, DebtNature, DebtStage
from peer_review.platform.memory_store import MemoryStore, ModelRunRecord


REPO_ROOT = Path(__file__).resolve().parents[3]


class TestPrivacyFieldExtraction:
    def test_extract_all_fields(self):
        d = Debt(
            debtor_name="张三",
            amount=50000,
            debtor_id="110101199001011234",
            debtor_region="杭州",
            evidence=["借条", "转账记录"],
            nature=DebtNature.PRIVATE_LOAN,
            stage=DebtStage.NEGOTIATION,
        )
        fields = _extract_privacy_fields(d)
        assert fields["debtor_name"] == "张三"
        assert fields["id_number"] == "110101199001011234"
        assert fields["amount"] == 50000
        assert fields["case_evidence"] == "借条, 转账记录"
        assert fields["debtor_region"] == "杭州"

    def test_empty_fields_omitted(self):
        d = Debt(debtor_name="张三", amount=50000)
        fields = _extract_privacy_fields(d)
        assert "id_number" not in fields
        assert "case_evidence" not in fields


class TestPlanUsesApi:
    def test_default_plan_uses_api(self):
        assert _plan_uses_api(REPO_ROOT, "default") is True

    def test_all_local_plan_no_api(self):
        assert _plan_uses_api(REPO_ROOT, "all-local") is False

    def test_high_quality_plan_uses_api(self):
        assert _plan_uses_api(REPO_ROOT, "high-quality") is True

    def test_fast_plan_uses_api(self):
        assert _plan_uses_api(REPO_ROOT, "fast") is True


class TestEstimateCost:
    def test_default_cost(self):
        cost = _estimate_cost("default", REPO_ROOT)
        assert 0.01 < cost < 0.03

    def test_all_local_cost(self):
        cost = _estimate_cost("all-local", REPO_ROOT)
        assert cost == 0.0

    def test_high_quality_cost(self):
        cost = _estimate_cost("high-quality", REPO_ROOT)
        assert 0.05 < cost < 0.15


class TestMemoryStoreRecord:
    def test_record_and_retrieve(self, tmp_path):
        db = MemoryStore(tmp_path / "memory.db")
        record = ModelRunRecord(
            run_id="r1",
            case_hash="abc",
            plan_id="default",
            models_used={"primary_expert": "local-qwen35b"},
            total_time_seconds=120,
            total_cost_usd=0.02,
            divergence_score=0.1,
        )
        db.record_run(record)
        rows = db.get_plan_comparison(days=30)
        assert len(rows) == 1
        assert rows[0]["plan_id"] == "default"

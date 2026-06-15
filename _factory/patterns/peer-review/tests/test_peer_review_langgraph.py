# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 02:35:00 CST
"""Peer-Review LangGraph 新架构测试套件

覆盖：
- 配置加载与交叉验证（RoutingPlanEngine）
- 数据出境门控（DataPrivacyGate）
- 分层决策引擎（DecisionEngine）
- LangGraph 图构建与基础运行（无需 LLM）
"""
from __future__ import annotations

from pathlib import Path

import pytest

from peer_review.config import ConfigurationError, load_all_configs
from peer_review.graph.review_graph import build_review_graph
from peer_review.graph.state import ReviewState
from peer_review.orchestrator import run_langgraph_review
from peer_review.platform.data_privacy_gate import DataPrivacyGate, GateDecisionType
from peer_review.platform.decision_engine import DecisionContext, DecisionEngine, DecisionType
from peer_review.platform.knowledge_hub import KnowledgeHub
from peer_review.platform.memory_store import MemoryStore, ModelRunRecord
from peer_review.platform.routing_plan_engine import RoutingPlanEngine


REPO_ROOT = Path(__file__).resolve().parents[4]


# ── 配置加载测试 ──

class TestRoutingPlanEngine:
    def test_load_all_configs(self):
        cfg = load_all_configs(REPO_ROOT)
        assert cfg.routing.active_plan == "default"
        assert "local-qwen35b" in cfg.models.models
        assert "deepseek-flash" in cfg.models.models

    def test_active_plan_primary_model(self):
        engine = RoutingPlanEngine(REPO_ROOT)
        model = engine.get_model_for_node("primary_expert")
        assert model.model_id == "qwen3.5:35b-a3b-q8_0"
        assert model.type.value == "local"

    def test_plan_menu(self):
        engine = RoutingPlanEngine(REPO_ROOT)
        summaries = engine.list_plans_summary(available_mem_gb=64)
        ids = [s.plan_id for s in summaries]
        assert "default" in ids
        assert "high-quality" in ids
        assert "all-local" in ids
        assert "fast" in ids

    def test_high_quality_memory_check(self):
        engine = RoutingPlanEngine(REPO_ROOT)
        # high-quality 方案有 3 个 API 并行，无本地模型，内存安全
        result = engine.check_parallel_memory_safety("high-quality", 64)
        assert result.is_safe is True

    def test_all_local_memory_check(self):
        engine = RoutingPlanEngine(REPO_ROOT)
        # all-local 方案 3 个本地模型顺序执行，但 memory_required_gb 求和仍可能 > 64
        result = engine.check_parallel_memory_safety("all-local", 64)
        # 该方案中 reviewer 执行模式是 sequential_isolated，不计入并行内存
        assert result.is_safe is True


# ── 数据出境门控测试 ──

class TestDataPrivacyGate:
    def test_local_only_blocked_for_api(self):
        gate = DataPrivacyGate(REPO_ROOT / "config" / "privacy_policy.yaml")
        result = gate.check({"debtor_name": "张三"}, "chinese_api")
        assert result.allowed is False
        assert "debtor_name" in result.blocked_fields

    def test_allow_field_passes(self):
        gate = DataPrivacyGate(REPO_ROOT / "config" / "privacy_policy.yaml")
        result = gate.check({"compliance_analysis": "合法"}, "chinese_api")
        assert result.allowed is True

    def test_masked_field_passes(self):
        gate = DataPrivacyGate(REPO_ROOT / "config" / "privacy_policy.yaml")
        result = gate.check({"amount": 50000}, "chinese_api")
        assert result.allowed is True
        assert "约 5 万元" in result.preview["amount"]

    def test_unknown_endpoint_blocked(self):
        gate = DataPrivacyGate(REPO_ROOT / "config" / "privacy_policy.yaml")
        result = gate.check({"compliance_analysis": "合法"}, "unknown_api")
        assert result.allowed is False


# ── 分层决策引擎测试 ──

class TestDecisionEngine:
    def test_iron_gate_blocks_violence(self):
        engine = DecisionEngine()
        decision = engine.decide(
            DecisionContext(case_text="债务人失联，考虑上门堵人")
        )
        assert decision.decision == DecisionType.BLOCKED
        assert "暴力" in decision.reason

    def test_iron_gate_blocks_privacy_leak(self):
        engine = DecisionEngine()
        decision = engine.decide(
            DecisionContext(proposed_strategy="发朋友圈公开债务人信息")
        )
        assert decision.decision == DecisionType.BLOCKED

    def test_clean_case_passes(self):
        engine = DecisionEngine()
        decision = engine.decide(
            DecisionContext(case_text="张三欠钱，有借条，想起诉")
        )
        assert decision.decision == DecisionType.APPROVED


# ── LangGraph 图测试 ──

class TestLangGraphReview:
    def test_graph_compiles(self):
        engine = RoutingPlanEngine(REPO_ROOT)
        kh = KnowledgeHub(
            knowledge_root=REPO_ROOT / "_factory" / "experts",
            skills_root=REPO_ROOT / "_factory" / "skills",
        )
        graph = build_review_graph(engine, kh)
        assert graph is not None
        assert "primary_expert" in graph.nodes
        assert "consensus_builder" in graph.nodes
        assert "human_review_gate" in graph.nodes

    def test_run_langgraph_review_no_llm(self):
        """无 LLM 时仍应完成图结构并返回降级内容"""
        result = run_langgraph_review("张三欠李四50000元，有借条。", project_root=REPO_ROOT)
        assert "primary_analysis" in result
        assert "consensus" in result
        assert len(result.get("reviewer_opinions", [])) == 3
        assert "models_used" in result

    def test_case_context_preserved(self):
        result = run_langgraph_review("测试案件", project_root=REPO_ROOT)
        assert result.get("case_context") == "测试案件"


# ── MemoryStore 测试 ──

class TestMemoryStore:
    def test_record_and_query(self, tmp_path):
        db = MemoryStore(tmp_path / "memory.db")
        record = ModelRunRecord(
            run_id="r1",
            case_hash="abc",
            plan_id="default",
            models_used={"primary_expert": "local-qwen35b"},
            total_time_seconds=120,
            total_cost_usd=0.02,
            divergence_score=0.1,
            human_quality_score=4,
            adopted_by_user=True,
        )
        db.record_run(record)
        rows = db.get_plan_comparison(days=30)
        assert len(rows) == 1
        assert rows[0]["plan_id"] == "default"


# ── LLM 客户端节点级隐私二次校验 ──

class TestLLMClientPrivacy:
    def test_api_call_blocked_without_approval(self):
        from peer_review.llm_client import chat
        from peer_review.config import load_models_config

        models = load_models_config(REPO_ROOT / "config" / "models.yaml")
        model_cfg = models.models["deepseek-flash"]
        resp = chat(
            model_cfg,
            [{"role": "user", "content": "test"}],
            privacy_context={
                "data_fields": {"debtor_name": "张三"},
                "endpoint": "chinese_api",
                "approved": False,
            },
        )
        assert resp.blocked is True
        assert "节点级数据出境被阻断" in resp.content

    def test_api_call_allowed_with_approval(self):
        from peer_review.llm_client import chat
        from peer_review.config import load_models_config

        models = load_models_config(REPO_ROOT / "config" / "models.yaml")
        model_cfg = models.models["deepseek-flash"]
        resp = chat(
            model_cfg,
            [{"role": "user", "content": "test"}],
            privacy_context={
                "data_fields": {"debtor_name": "张三"},
                "endpoint": "chinese_api",
                "approved": True,
            },
        )
        # 网关/Ollama 不可用，但不应被隐私门阻断
        assert resp.blocked is False

    def test_local_call_no_privacy_check(self):
        from peer_review.llm_client import chat
        from peer_review.config import load_models_config

        models = load_models_config(REPO_ROOT / "config" / "models.yaml")
        model_cfg = models.models["local-qwen35b"]
        resp = chat(
            model_cfg,
            [{"role": "user", "content": "test"}],
            privacy_context={
                "data_fields": {"debtor_name": "张三"},
                "endpoint": "local_model",
                "approved": False,
            },
        )
        # 本地模型不触发隐私检查
        assert resp.blocked is False


# ── 端到端测试（模拟 LLM 响应）──

class TestEndToEndWithMockLLM:
    def test_full_review_pipeline_with_mocks(self, monkeypatch):
        from peer_review.orchestrator import run_langgraph_review
        from peer_review.llm_client import LLMResponse

        def mock_gateway(model_name, messages, timeout=120):
            return LLMResponse(
                content=f"[模拟 API {model_name} 回复]",
                model=model_name,
            )

        def mock_ollama(model_cfg, messages):
            return LLMResponse(
                content=f"[模拟本地 {model_cfg.display_name} 回复]",
                model=model_cfg.model_id,
            )

        monkeypatch.setattr("peer_review.llm_client._call_litellm_gateway", mock_gateway)
        monkeypatch.setattr("peer_review.llm_client._call_ollama_direct", mock_ollama)

        result = run_langgraph_review(
            "张三欠李四50000元，有借条。",
            project_root=REPO_ROOT,
            plan_id="default",
            data_fields={"debtor_name": "张三", "amount": 50000},
            privacy_endpoint="chinese_api",
            privacy_approved=True,
            use_live=False,
        )
        assert "primary_analysis" in result
        assert "consensus" in result
        assert len(result.get("reviewer_opinions", [])) == 3
        assert result.get("thread_id") is not None


# ── HITL 恢复测试 ──

class TestHITLContinue:
    def test_continue_requires_existing_thread(self):
        from peer_review.orchestrator import continue_langgraph_review

        with pytest.raises(ValueError):
            continue_langgraph_review("non-existent-thread", project_root=REPO_ROOT, use_live=False)

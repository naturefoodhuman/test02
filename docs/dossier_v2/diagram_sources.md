<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间）：2026-06-20 22:30:00 CST
-->

# Diagram Sources – 图表证据映射

## 1. System Context View
- **Source**: Mermaid graph TB in PROJECT_DOSSIER_V2.md §4
- **Evidence**: 
  - Smart Proxy entry: `_infra/smart_proxy_streaming.py:112`
  - Model backends: `config/models.yaml`
  - Peer-Review Engine: `_factory/patterns/peer-review/src/peer_review/orchestrator.py`
  - KnowledgeHub: `.../platform/knowledge_hub.py`
  - PrivacyGate: `.../platform/data_privacy_gate.py`
- **Trust Boundary**: local_model = trusted, DeepSeek API = external_untrusted

## 2. Container View
- **Source**: Structured text list in §4
- **Components**:
  - smart_proxy_streaming (FastAPI :4000)
  - peer_review_orchestrator (LangGraph, CLI triggered)
  - knowledge_hub (ChromaDB local)
  - memory_store (runtime/checkpoints.sqlite)
  - Model Servers (8080/8082/8084/11434 independent)
- **Evidence**: `HANDOFF.md §3`, `docs/PROJECT_STATE.md`

## 3. Component View – Peer-Review
- **Source**: Text component diagram in §4
- **Key classes**:
  - `AppConfig` – `config/schemas.py:230`
  - `RoutingPlanEngine` – `platform/routing_plan_engine.py`
  - `LLMBackendFactory` – `llm_client.py:250`
  - `ReviewState` – `graph/state.py:15`
  - Nodes: `primary_expert`, `reviewer`, `consensus`, `decision`, `record_run` – `graph/nodes/*.py`
- **Evidence mapping**: see evidence_index.csv E-001, E-003, E-010

## 4. Runtime View – 策略生成主链路
- **Source**: Sequential list §4 Runtime View
- **Trigger**: `scripts/benchmark_test.py`
- **Steps**: load_all_configs → build_review_graph → primary_expert → reviewer(s) parallel → consensus → decision → record_run
- **Evidence**:
  - execution entry: `graph/execution.py:25`
  - chat call: `llm_client.py:307`
  - SSE stream: `smart_proxy_streaming.py:133`
- **Latency observed**: 1132.5s – `docs/PROJECT_STATE.md §4`

## 5. Deployment View
- **Source**: Text deployment diagram §4
- **Node**: Mac M1 Max 64GB, macOS
- **Startup**: `bash scripts/forge-start.sh` → `python3 _infra/smart_proxy.py`
- **Model launcher**: `ensure_server()` – `smart_proxy_streaming.py:72` – AppleScript
- **Config**: `_infra/.env`
- **Rollback**: git revert
- **Evidence**: `HANDOFF.md §3`

## 6. Codebase Topology Map
- **Source**: §5 Codebase Topology
- **Layers**:
  - _infra/ – gateway / CLI
  - _factory/patterns/peer-review/ – core engine
  - _factory/patterns/* – scaffolds
  - projects/_TEMPLATE/ – incubation template
  - projects/debt-collection/ – real project
- **Coupling hotspots**:
  - `llm_client.py` – evidence E-039
  - `config/schemas.py`
  - `routing_plan_engine.py`
- **Change amplifiers**:
  - `config/models.yaml`
  - `ReviewState`
  - `smart_proxy_streaming.py` field whitelist

## 7. Data Flow – Privacy Gate
- **Source**: §7 Data Architecture + config/privacy_policy.yaml
- **Flow**: LLM request → `_privacy_check()` in `llm_client.py:265` → Policy lookup → local_only block / human_approve prompt / mask_then_allow transform / allow pass
- **Fields**: debtor_name (local_only), id_number (human_approve), amount (mask_then_allow), compliance_analysis (allow)
- **Evidence**: `config/privacy_policy.yaml`, `llm_client.py:265`

## 8. Build/Test/Release Chain
- **Source**: §8
- **Build**: uv / pip, per-pattern pyproject.toml
- **Test**: forge_tools 19 passed, peer-review integration test exists but not CI
- **Release**: git tag manual, CHANGELOG.md manual
- **Deploy**: git clone + setup.sh + .env manual
- **Evidence**: `E-012`, `E-021`, `E-040`

---

All diagrams are text/Mermaid based, no binary assets. Original mermaid sources embedded in PROJECT_DOSSIER_V2.md §4.

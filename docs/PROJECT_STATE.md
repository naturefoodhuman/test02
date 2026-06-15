<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-15 02:40:00 CST
-->

# PROJECT STATE —— 当前进度快照

## 架构阶段
- **Phase A 线 1（LangGraph 迁移）**: 🚧 已启动，核心 StateGraph / HUB-SPOKE / 平台层已落地
- **Phase A 线 2（双文件体系 + DataPrivacyGate）**: ✅ models.yaml / routing_plans.yaml / privacy_policy.yaml 已就位，平台层已接入
- **Phase B（能力激活）**: ⏳ 待 LangGraph 验证稳定后启动
- **Phase C（工厂能力）**: ⏳ 待后续

## 核心资产状态
- **专家系统**: `debt-lawyer.expert` (primary, 本地 R1 驱动，知识库已就位)
- **评审专家团**: `risk-assessor` / `compliance-auditor` / `execution-strategist` (reviewers)
- **LangGraph 评审引擎**: `_factory/patterns/peer-review/src/peer_review/graph/` 已构建
  - `graph/review_graph.py`: HUB-SPOKE 状态图
  - `graph/nodes/primary_expert.py`: 主专家节点（含决策引擎铁闸）
  - `graph/nodes/reviewer.py`: HUB-SPOKE 评审者节点（信息屏蔽）
  - `graph/nodes/consensus.py`: 汇总 + 分歧检测
  - `graph/checkpointer.py`: SqliteSaver 检查点
- **平台层**:
  - `platform/routing_plan_engine.py`: A/B 文件交叉校验 + 方案菜单 + 内存预检
  - `platform/data_privacy_gate.py`: privacy_policy.yaml 策略执行
  - `platform/memory_store.py`: ModelRunRecord 记录
  - `platform/knowledge_hub.py`: 知识统一接口
  - `platform/decision_engine.py`: 铁闸 + AI 参考 + AI 生成
- **配置层**: `config/models.yaml` / `config/routing_plans.yaml` / `config/privacy_policy.yaml` 已按最终架构设计实现
- **CLI 入口**: `debt review` 已切换到 LangGraph 路径（`--plan` 临时指定方案）
- **测试**: `peer-review` 新测试套件 16 cases 全通过；`debt-collection` 22 cases 全通过

## 已知限制 / 待完成
- [ ] 真实 LLM 调用需启动 LiteLLM 网关或 Ollama 服务（当前降级为提示信息）
- [ ] 评审节点尚未接入 DataPrivacyGate 在运行时的人工确认门（策略层已就绪，执行层待挂）
- [ ] MemoryStore 尚未在 `debt review` 结束后自动写入记录（类已就绪，CLI 待挂）
- [ ] 流式输出体验待优化（当前已有节点级进度打印）
- [ ] HITL 中断后恢复流程待补充文档与 CLI 指令
- [ ] 旧 Agno 文件 (`agent_factory.py`, `knowledge_loader.py`, `team_orchestrator.py`) 仍保留，待 LangGraph 稳定 2 周后删除
- [ ] `docs/UPGRADE_LEARNINGS.md` 待最终阶段补齐

## 运行依赖
沙箱/真机需安装：
```bash
pip install -e projects/debt-collection -e _factory/patterns/peer-review
pip install langgraph>=1.0.10 langgraph-checkpoint-sqlite>=3.0.1 \
            litellm>=1.40 chromadb>=0.6 llama-index-core>=0.12 \
            pydantic>=2.10 pyyaml rich ollama httpx
```

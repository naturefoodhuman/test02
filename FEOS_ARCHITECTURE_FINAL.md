# FORGE Escalation OS（FEOS）最终版架构设计方案

> 版本：Architecture V2 Final  
> 定位：FORGE Factory 的 **Case Intelligence Operating System**  
> 当前主通道：**Artifact 导出 → 人工粘贴给 GPT/Claude → 粘贴回复回来**  
> 未来备用通道：API / MCP / Browser Automation / Cloud Agent  
> 核心范式：**Case First + Evidence Graph + Context Compiler + Gateway Layer + Verification + Knowledge Distillation**

---

# 0. 最终架构判断


最终架构应当是：

```text
FORGE Task / Local Agent
        │
        ▼
Failure & Uncertainty Detector
        │
        ▼
Escalation Case Manager
        │
        ▼
Evidence Collection Layer
        │
        ▼
Case Graph Builder
        │
        ▼
Similarity Retrieval
        │
        ▼
Hypothesis Manager
        │
        ▼
Policy Plane
        │
        ▼
Context Compiler
        │
        ▼
Escalation Package Builder
        │
        ▼
Gateway Layer
        ├── Clipboard Gateway     ← 当前主流程
        ├── API Gateway           ← 未来
        ├── MCP Gateway           ← 未来
        ├── Browser Gateway       ← 未来
        └── Cloud Agent Gateway   ← 未来
        │
        ▼
External Reasoning Session
        │
        ▼
Response Ingestion Pipeline
        │
        ▼
Verification Layer
        │
        ▼
Execution Planner
        │
        ▼
Local Execution Agent
        │
        ▼
Execution Tracker
        │
        ▼
Outcome Evaluator
        │
        ▼
Knowledge Distillation
        │
        ▼
Knowledge OS
```

---

# 1. FEOS 的最终定位

## 1.1 FEOS 是什么

FEOS 是 FORGE Factory 的一级基础设施，用于管理本地 AI Agent 在开发、调试、架构、重构、研究、MCP 工程等任务中遇到的能力边界。

它负责：

- 发现失败和不确定性
- 建立 Escalation Case
- 收集客观证据
- 构建 Case Graph
- 检索历史相似案例
- 生成高质量升级材料
- 通过 Clipboard / API / MCP / Browser Gateway 连接外部强模型
- 导入外部回复
- 结构化解析建议
- 验证建议是否安全可执行
- 生成执行计划
- 跟踪执行结果
- 蒸馏知识进入 Knowledge OS

## 1.2 FEOS 不是什么

FEOS 不是：

- Prompt 生成器
- HELP_REQUEST.md 生成器
- GPT 问答助手
- 单次求助工具
- 外部模型代理
- 自动联网系统
- 自动执行外部建议的系统

FEOS 的核心不是 Prompt，而是：

> **Escalation Case + Evidence Graph + Context Package + Verification + Knowledge Lifecycle**

---

# 2. 核心设计原则

## 2.1 Case First

所有升级行为都围绕 `Escalation Case`。

Prompt、Markdown、JSON、MCP Message、API Request 都只是 Case 的不同视图。

## 2.2 Evidence First

所有结论必须来自证据。

证据包括：

- Git Diff
- Stack Trace
- Runtime Log
- Tool Call
- MCP Call
- Config
- Environment
- Dependency
- Prompt
- Agent Plan
- Test Result
- User Goal
- Previous Attempt

禁止仅凭 Agent 主观总结构建求助材料。

## 2.3 Graph First

FEOS 内部不以文档为主，而以 Graph 为主。

Document 是 Graph 的渲染结果。

## 2.4 Context First

真正交给外部模型的是 `Context Package`。

Prompt 只是最后的文本渲染。

## 2.5 Verification First

外部模型只提供推理建议。  
任何建议必须经过本地验证后才能执行。

## 2.6 Clipboard First, API Ready

当前必须支持：

```text
导出 Artifact → 人工粘贴给 GPT/Claude → 粘贴回复回来
```

这是正式主流程，不是临时 hack。

同时架构必须预留：

- API Gateway
- MCP Gateway
- Browser Automation Gateway
- Cloud Agent Gateway

## 2.7 Human Decision

人不应该负责整理上下文。  
人只负责：

- 确认是否升级
- 确认外发内容
- 选择目标模型
- 粘贴内容
- 粘贴回复
- 审批高风险执行

## 2.8 Model Agnostic

GPT、Claude、Gemini、DeepSeek、Qwen、未来模型都只是 Provider。

核心 Case 不绑定任何模型。

## 2.9 Knowledge Lifecycle

知识不是简单保存 GPT 回复。  
知识必须经过：

```text
Captured → Verified → Indexed → Retrieved → Reused → Deprecated → Archived
```

---

# 3. 系统边界

## 3.1 FEOS 负责的事情

FEOS 负责：

1. 失败检测
2. Case 创建
3. 证据采集
4. Graph 构建
5. 相似案例检索
6. 假设管理
7. 策略检查
8. 上下文编译
9. Artifact 导出
10. Gateway 会话管理
11. 回复导入
12. 回复结构化解析
13. 建议验证
14. 执行计划生成
15. 执行追踪
16. 结果评估
17. 知识蒸馏
18. 审计和观测

## 3.2 FEOS 不负责的事情

FEOS 不直接负责：

1. 实际代码编辑  
   由 Local Coding Agent / FORGE Executor 执行。

2. 实际测试运行  
   由 Test Runner / CI / Sandbox 执行。

3. 强模型推理本身  
   由外部 GPT / Claude / Gemini 等完成。

4. Knowledge OS 的底层存储实现  
   FEOS 只负责写入标准化知识对象。

5. 用户最终决策  
   用户拥有最终审批权。

---

# 4. 顶层模块设计

最终 FEOS 拆为 14 个核心子系统。

```text
FEOS
├── 01 Failure & Uncertainty Detector
├── 02 Escalation Case Manager
├── 03 Evidence Collection Layer
├── 04 Case Graph Builder
├── 05 Similarity Retrieval Engine
├── 06 Hypothesis Manager
├── 07 Policy Plane
├── 08 Context Compiler
├── 09 Escalation Package Builder
├── 10 Gateway Layer
├── 11 Response Ingestion Pipeline
├── 12 Verification Layer
├── 13 Execution Tracking Layer
├── 14 Knowledge Distillation Layer
```

---

# 5. 核心对象：Escalation Case

## 5.1 Escalation Case 是系统主实体

所有数据围绕 Case。

一个 Case 表示一次明确的调查和升级过程。

## 5.2 Case 生命周期

```text
Draft
  ↓
Created
  ↓
CollectingEvidence
  ↓
GraphBuilding
  ↓
Investigating
  ↓
PolicyChecking
  ↓
ContextCompiling
  ↓
PackageGenerated
  ↓
WaitingHumanExport
  ↓
WaitingExternalResponse
  ↓
ResponseImported
  ↓
ParsingResponse
  ↓
Verifying
  ↓
PlanningExecution
  ↓
Executing
  ↓
EvaluatingOutcome
  ↓
Resolved / Unresolved / Abandoned
  ↓
DistillingKnowledge
  ↓
Archived
```

## 5.3 Case 状态说明

| 状态 | 含义 |
|---|---|
| Draft | 初步检测到问题，但还未正式创建 |
| Created | Case 已创建 |
| CollectingEvidence | 正在采集证据 |
| GraphBuilding | 正在构建 Case Graph |
| Investigating | 本地分析和假设生成 |
| PolicyChecking | 检查安全、脱敏、预算、审批策略 |
| ContextCompiling | 编译上下文 |
| PackageGenerated | 已生成升级包 |
| WaitingHumanExport | 等待用户复制粘贴到外部模型 |
| WaitingExternalResponse | 等待用户粘贴外部回复 |
| ResponseImported | 回复已导入 |
| ParsingResponse | 正在结构化解析回复 |
| Verifying | 正在验证外部建议 |
| PlanningExecution | 生成执行计划 |
| Executing | 本地执行中 |
| EvaluatingOutcome | 评估执行结果 |
| Resolved | 已解决 |
| Unresolved | 未解决，可进入下一轮升级 |
| Abandoned | 用户放弃 |
| DistillingKnowledge | 知识蒸馏中 |
| Archived | Case 归档 |

---

# 6. Case 数据模型

## 6.1 Escalation Case Schema

```yaml
case:
  id: "case_2026_06_30_001"
  title: "MCP tool call fails with schema validation error"
  project_id: "forge_factory"
  repo_id: "forge-core"
  task_id: "task_abc123"

  status: "Investigating"
  severity: "high"              # low | medium | high | critical
  category: "mcp_issue"         # bug | architecture | performance | security | refactor | mcp_issue | unknown
  created_at: "2026-06-30T10:30:00Z"
  updated_at: "2026-06-30T11:10:00Z"

  owner:
    user_id: "local_user"
    agent_id: "local_coding_agent"

  problem:
    user_goal: "让 MCP tool call 正常返回结构化结果"
    expected_behavior: "tool call 应通过 schema validation"
    actual_behavior: "调用失败，返回 schema validation error"
    failure_signature: "ValidationError: required field 'result' missing"
    reproduction: "运行 forge agent run mcp-test"

  trigger:
    type: "repeated_failure"
    attempts: 3
    local_confidence: 0.42
    escalation_score: 0.81
    reason: "相同异常连续出现，本地 Agent 已尝试三种修复仍失败"

  links:
    evidence_graph_id: "graph_case_001"
    package_ids:
      - "pkg_001"
    external_session_ids:
      - "session_clipboard_gpt_001"
    response_ids:
      - "resp_001"

  policy:
    sensitivity_level: "internal"
    export_allowed: true
    requires_human_review: true
    redaction_profile: "default_strict"

  outcome:
    status: null
    resolution_summary: null
    root_cause: null
    fixed_by: null

  audit:
    created_by: "feos.detector"
    last_transition_by: "human"
    external_exports:
      - "export_001"
```

---

# 7. Failure & Uncertainty Detector

## 7.1 作用

判断什么时候应该进入 FEOS。

不是所有失败都升级。  
FEOS 应该在本地模型进入低效、重复、上下文污染或能力边界时介入。

## 7.2 输入信号

```yaml
detector_inputs:
  execution_failures:
    - error_type
    - stack_trace
    - failed_command
    - failed_test
    - failing_tool_call

  agent_behavior:
    - repeated_plan
    - repeated_file_edit
    - circular_reasoning
    - uncertainty_statement
    - hallucinated_reference
    - tool_call_loop

  context_health:
    - context_size
    - contradiction_count
    - stale_context_ratio
    - unresolved_assumption_count

  task_metadata:
    - severity
    - user_priority
    - deadline
    - blast_radius
```

## 7.3 Escalation Score

FEOS 使用评分，而不是固定规则。

```yaml
escalation_score:
  repeated_failure_score: 0.25
  uncertainty_score: 0.20
  error_stability_score: 0.15
  task_complexity_score: 0.15
  context_pollution_score: 0.10
  missing_knowledge_score: 0.10
  user_priority_score: 0.05
  total: 0.80
```

## 7.4 默认触发策略

```yaml
trigger_policy:
  auto_create_case_if_score_above: 0.70
  suggest_case_if_score_above: 0.50
  continue_local_if_score_below: 0.50

  hard_triggers:
    - same_error_repeated_2_times
    - tool_call_loop_detected
    - local_agent_declares_no_new_strategy
    - context_window_exceeded
    - security_sensitive_failure
    - architecture_decision_deadlock
```

---

# 8. Evidence Collection Layer

## 8.1 设计目标

采集客观事实，不是生成总结。

## 8.2 Collector 插件体系

```text
Evidence Collectors
├── Git Collector
├── Diff Collector
├── Code Collector
├── AST Collector
├── Log Collector
├── Stack Trace Collector
├── Runtime Collector
├── Test Collector
├── Dependency Collector
├── Config Collector
├── Environment Collector
├── Tool Call Collector
├── MCP Collector
├── Prompt Collector
├── Agent Plan Collector
├── Memory Collector
├── Knowledge Collector
├── Architecture Collector
├── ADR Collector
├── User Input Collector
└── Previous Attempt Collector
```

## 8.3 Evidence Schema

```yaml
evidence:
  id: "ev_stacktrace_001"
  case_id: "case_2026_06_30_001"

  type: "stack_trace"
  subtype: "python_validation_error"

  source:
    collector: "StackTraceCollector"
    origin: "runtime_log"
    file: "logs/agent-run.log"
    line_start: 120
    line_end: 158

  content:
    raw_ref: "evidence/raw/ev_stacktrace_001.txt"
    text_preview: "ValidationError: required field 'result' missing"
    normalized: {}

  metadata:
    timestamp: "2026-06-30T10:31:00Z"
    hash: "sha256:abc..."
    provenance: "captured_from_runtime"
    replayable: true

  quality:
    confidence: 0.98
    importance: 0.95
    freshness: 1.0
    completeness: 0.90

  security:
    sensitivity: "internal"
    contains_secret: false
    contains_pii: false
    redaction_status: "not_needed"

  relations:
    supports:
      - "hyp_schema_mismatch"
    refutes: []
    relates:
      - "ev_toolcall_001"
      - "ev_diff_003"
```

## 8.4 Evidence 重要性评分

```yaml
importance_weights:
  stack_trace: 0.95
  failing_test: 0.95
  git_diff: 0.90
  tool_call_trace: 0.90
  mcp_call_trace: 0.90
  config: 0.80
  dependency_lock: 0.80
  runtime_env: 0.70
  architecture_doc: 0.65
  agent_prompt: 0.60
  conversation_history: 0.45
  readme: 0.30
```

---

# 9. Case Graph

## 9.1 为什么不是 Evidence Graph，而是 Case Graph

最终版建议叫 **Case Graph**。

因为图里不只有 Evidence，还包括：

- Evidence
- Fact
- Hypothesis
- Decision
- Action
- Outcome
- Knowledge Candidate

## 9.2 节点类型

```yaml
node_types:
  Evidence:
    description: "原始或标准化证据"

  Fact:
    description: "由证据支持的事实"

  Hypothesis:
    description: "待验证的假设"

  Decision:
    description: "人或系统做出的决策"

  Action:
    description: "已执行或计划执行的动作"

  Outcome:
    description: "动作结果"

  Constraint:
    description: "项目约束、架构原则、禁止事项"

  KnowledgeCandidate:
    description: "可沉淀为知识的候选经验"
```

## 9.3 边类型

```yaml
edge_types:
  supports: "A 支持 B"
  refutes: "A 反驳 B"
  depends_on: "A 依赖 B"
  causes: "A 导致 B"
  generated_by: "A 由 B 生成"
  resolves: "A 解决 B"
  attempts_to_resolve: "A 尝试解决 B"
  violates: "A 违反 B"
  compatible_with: "A 与 B 兼容"
  duplicates: "A 与 B 重复"
  similar_to: "A 与历史 Case 相似"
  derived_from: "A 来源于 B"
```

## 9.4 Graph 存储结构

```yaml
case_graph:
  id: "graph_case_001"
  case_id: "case_2026_06_30_001"

  nodes:
    - id: "ev_stacktrace_001"
      type: "Evidence"
      label: "ValidationError stack trace"

    - id: "fact_missing_result_field"
      type: "Fact"
      label: "MCP response lacks required field result"

    - id: "hyp_schema_mismatch"
      type: "Hypothesis"
      label: "Tool response schema mismatches MCP contract"

  edges:
    - from: "ev_stacktrace_001"
      to: "fact_missing_result_field"
      type: "supports"
      confidence: 0.98

    - from: "fact_missing_result_field"
      to: "hyp_schema_mismatch"
      type: "supports"
      confidence: 0.85
```

---

# 10. Similarity Retrieval Engine

## 10.1 作用

升级前先查历史，避免重复问 GPT。

## 10.2 检索对象

```yaml
retrieval_targets:
  - previous_cases
  - failure_patterns
  - resolution_patterns
  - anti_patterns
  - playbooks
  - architecture_decisions
  - rejected_solutions
  - tool_specific_known_issues
```

## 10.3 检索维度

```yaml
similarity_features:
  error_signature: 0.30
  stack_trace_embedding: 0.20
  changed_files: 0.15
  dependency_versions: 0.10
  tool_call_pattern: 0.10
  project_module: 0.10
  natural_language_problem: 0.05
```

## 10.4 输出

```yaml
similar_cases:
  - case_id: "case_2026_05_12_003"
    similarity: 0.87
    resolution: "Add result field to MCP tool response wrapper"
    reused_successfully: true
    warnings:
      - "Only applies to MCP SDK v1.8+"
```

---

# 11. Hypothesis Manager

## 11.1 作用

维护问题调查中的候选假设，而不是让 Agent 散乱猜测。

## 11.2 Hypothesis Schema

```yaml
hypothesis:
  id: "hyp_schema_mismatch"
  case_id: "case_2026_06_30_001"

  title: "MCP tool response schema mismatch"
  description: "工具返回对象缺少 MCP schema 要求的 result 字段"

  status: "Supported"   # Proposed | Testing | Supported | Rejected | Confirmed

  confidence: 0.82

  supporting_evidence:
    - "ev_stacktrace_001"
    - "ev_toolcall_001"

  counter_evidence: []

  tests_to_confirm:
    - "Inspect MCP tool response adapter"
    - "Compare actual response with MCP schema"

  related_actions:
    - "act_inspect_adapter"

  created_by: "local_agent"
  updated_at: "2026-06-30T10:45:00Z"
```

---

# 12. Policy Plane

## 12.1 作用

所有外发前必须经过 Policy Plane。

Policy Plane 是安全、预算、审批、模型策略的统一控制层。

## 12.2 Policy 类型

```yaml
policy_domains:
  security:
    - secret_detection
    - pii_detection
    - internal_url_redaction
    - credential_redaction
    - proprietary_code_policy

  export:
    - export_allowed
    - attachment_allowed
    - max_file_size
    - allowed_evidence_types

  model:
    - allowed_providers
    - preferred_provider
    - provider_risk_level

  budget:
    - max_tokens
    - max_rounds
    - max_external_sessions

  approval:
    - require_user_review
    - require_security_review
    - require_architect_review

  audit:
    - record_export_content_hash
    - keep_redacted_copy
    - keep_original_local_only
```

## 12.3 脱敏规则

```yaml
redaction_rules:
  secrets:
    patterns:
      - "api_key"
      - "secret"
      - "token"
      - "password"
      - "private_key"
    replacement: "[REDACTED_SECRET]"

  internal_paths:
    replacement: "[REDACTED_INTERNAL_PATH]"

  internal_domains:
    replacement: "[REDACTED_INTERNAL_DOMAIN]"

  user_personal_info:
    replacement: "[REDACTED_PII]"
```

## 12.4 Policy Check 输出

```yaml
policy_result:
  allowed: true
  requires_human_review: true
  redactions_applied: 8
  blocked_items: []
  warnings:
    - "2 internal file paths redacted"
    - "1 environment variable removed"
  export_hash: "sha256:def..."
```

---

# 13. Context Compiler

## 13.1 替代 Prompt Builder

最终版中不再存在 Prompt Builder。

替代为：

> **Context Compiler + Renderer Profile**

Context Compiler 负责选择、压缩、排序和打包上下文。

Renderer Profile 负责根据目标模型和 Gateway 渲染文本。

## 13.2 输入

```yaml
context_compiler_input:
  case_id: "case_2026_06_30_001"
  graph_id: "graph_case_001"
  target_provider: "chatgpt_web"
  gateway: "clipboard"
  task_type: "debug"
  token_budget: 24000
  policy_profile: "default_strict"
  renderer_profile: "gpt_markdown_debug"
```

## 13.3 输出

```yaml
context_package:
  id: "ctxpkg_001"
  case_id: "case_2026_06_30_001"
  token_budget: 24000
  estimated_tokens: 18200

  sections:
    - problem_summary
    - exact_question
    - relevant_facts
    - top_evidence
    - failed_attempts
    - suspected_hypotheses
    - project_constraints
    - relevant_code
    - logs
    - environment
    - requested_output_format

  omitted:
    - evidence_id: "ev_readme_001"
      reason: "low_importance"
    - evidence_id: "ev_old_log_003"
      reason: "duplicate"
```

## 13.4 Context Selection 策略

优先级：

```text
1. 直接错误证据
2. 最近相关 Diff
3. 失败命令 / 失败测试
4. Tool / MCP 调用链
5. 相关代码最小闭包
6. 配置和依赖
7. 项目约束
8. 已尝试方案
9. 相似历史案例
10. 背景说明
```

## 13.5 Context Compression 层级

```yaml
compression_layers:
  L0_raw:
    description: "原始证据，完整保留，本地存储，不一定外发"

  L1_cleaned:
    description: "去噪、脱敏、格式化后的证据"

  L2_structured:
    description: "结构化事实、调用链、错误签名"

  L3_summary:
    description: "高密度问题摘要"

  L4_prompt_view:
    description: "适合粘贴给模型的最终文本视图"
```

## 13.6 Packing 算法

```text
Input:
  Evidence Graph
  Hypotheses
  Token Budget
  Target Model Profile
  Policy Constraints

Steps:
  1. 计算 Evidence importance
  2. 删除 policy 禁止外发内容
  3. 聚合重复日志
  4. 保留错误上下文窗口
  5. 选择相关代码最小闭包
  6. 加入项目约束
  7. 加入已失败尝试
  8. 加入明确问题列表
  9. 加入输出格式要求
  10. 估算 token
  11. 若超预算，按 salience 逐层压缩
  12. 生成 Context Package
```

---

# 14. Escalation Package

## 14.1 定义

Escalation Package 是 FEOS 对外部模型的正式请求包。

它不是单个 Prompt，而是结构化对象。

## 14.2 Package Schema

```yaml
escalation_package:
  id: "pkg_001"
  case_id: "case_2026_06_30_001"
  created_at: "2026-06-30T11:00:00Z"

  target:
    gateway: "clipboard"
    provider: "chatgpt_web"
    renderer_profile: "gpt_markdown_debug"

  manifest:
    title: "MCP schema validation failure"
    task_type: "debug"
    severity: "high"
    project: "FORGE Factory"
    repository: "forge-core"

  problem:
    user_goal: "Fix MCP tool call schema validation error"
    expected_behavior: "Tool call returns valid MCP response"
    actual_behavior: "ValidationError: required field result missing"
    exact_questions:
      - "What is the most likely root cause?"
      - "Which file or adapter should be changed?"
      - "What minimal fix should be applied?"
      - "What tests should be added?"
      - "What risks should be checked before applying?"

  context:
    package_id: "ctxpkg_001"
    sections:
      - problem_summary
      - relevant_facts
      - evidence
      - failed_attempts
      - constraints
      - code_snippets
      - logs

  policy:
    redacted: true
    export_allowed: true
    external_execution_allowed: false
    note: "External AI should reason only. Do not assume ability to run code."

  attachments:
    - "attachments/relevant_diff.patch"
    - "attachments/stacktrace.txt"

  output_contract:
    expected_format:
      - root_cause_analysis
      - evidence_based_reasoning
      - recommended_fix
      - patch_or_pseudocode
      - validation_steps
      - risks
      - assumptions
      - follow_up_questions
```

---

# 15. Renderer Profiles

## 15.1 为什么需要 Renderer Profile

不同模型偏好的上下文结构不同。

但 FEOS 不应写死 Prompt Template。

因此使用 Renderer Profile。

## 15.2 当前必须支持的 Profile

```yaml
renderer_profiles:
  gpt_markdown_debug:
    gateway: "clipboard"
    provider: "chatgpt_web"
    style: "concise_structured"
    output_format: "markdown_sections"

  claude_markdown_architecture:
    gateway: "clipboard"
    provider: "claude_web"
    style: "long_context_structured"
    output_format: "markdown_with_artifacts"

  generic_markdown:
    gateway: "clipboard"
    provider: "unknown"
    style: "portable"
    output_format: "plain_markdown"

  api_json:
    gateway: "api"
    provider: "openai_or_anthropic"
    style: "structured"
    output_format: "json_schema"

  mcp_message:
    gateway: "mcp"
    provider: "mcp_reasoning_server"
    style: "tool_message"
    output_format: "mcp_payload"
```

---

# 16. Clipboard Gateway：当前正式主流程

## 16.1 设计原则

Clipboard Gateway 是一等 Gateway。

不是临时方案。

原因：

- 目前不能直接接强模型 API
- 用户需要控制外发内容
- 网页 GPT / Claude 仍是现实可用主路径
- 可保留审计和知识闭环
- 未来可无缝替换为 API/MCP

## 16.2 Clipboard Gateway 工作流

```text
1. FEOS 编译 Context Package
2. FEOS 生成 Escalation Package
3. FEOS 渲染 Markdown Artifact
4. FEOS 进行 Policy / Redaction 检查
5. 用户预览外发内容
6. 用户点击 Copy to Clipboard
7. 用户手动粘贴到 GPT / Claude 网页
8. 用户等待外部模型回复
9. 用户复制外部模型回复
10. 用户粘贴回 FEOS
11. FEOS 导入 Response
12. FEOS 解析、验证、生成执行计划
```

## 16.3 Clipboard Export Artifact

必须生成：

```text
.forge/feos/cases/<case_id>/exports/
├── clipboard.md               # 用户直接复制的文本
├── package.json               # 结构化包
├── manifest.json              # 元信息
├── redaction_report.json      # 脱敏报告
├── evidence_index.md          # 证据索引
├── attachments/
│   ├── relevant_diff.patch
│   ├── stacktrace.txt
│   └── logs_excerpt.txt
└── audit.json
```

## 16.4 clipboard.md 推荐结构

```markdown
# External Reasoning Request

## 1. Role

You are a senior AI agent systems engineer helping debug a real engineering issue.

## 2. Task

Please analyze the issue using only the evidence provided below.

## 3. Project Context

...

## 4. Problem

Expected:
...

Actual:
...

## 5. Exact Questions

1. What is the most likely root cause?
2. What evidence supports it?
3. What is the minimal safe fix?
4. What tests should validate it?
5. What risks should we check?

## 6. Relevant Facts

...

## 7. Evidence

### Evidence 1: Stack Trace

...

### Evidence 2: Tool Call Trace

...

### Evidence 3: Git Diff

...

## 8. Failed Attempts

...

## 9. Constraints

...

## 10. Required Response Format

Please respond in the following structure:

```yaml
root_cause:
  summary:
  confidence:
  evidence:

recommended_fix:
  description:
  files_to_change:
  patch_or_pseudocode:

validation_plan:
  commands:
  tests:

risks:
  - risk:
    mitigation:

assumptions:
  - assumption:

follow_up_questions:
  - question:
```
```

## 16.5 Clipboard Import

用户粘贴回复时，FEOS 创建：

```yaml
external_response:
  id: "resp_001"
  case_id: "case_2026_06_30_001"
  session_id: "session_clipboard_gpt_001"

  source:
    gateway: "clipboard"
    provider: "chatgpt_web"
    model_label: "user_selected_or_unknown"
    pasted_by: "human"
    pasted_at: "2026-06-30T11:30:00Z"

  content:
    raw_ref: "responses/resp_001_raw.md"
    hash: "sha256:xyz..."

  parse_status: "pending"
```

---

# 17. Gateway Layer

## 17.1 Gateway 抽象接口

所有 Gateway 都实现同一接口：

```typescript
interface EscalationGateway {
  prepare(package: EscalationPackage): GatewayPreparedRequest
  dispatch(request: GatewayPreparedRequest): GatewayDispatchResult
  receive(session: ExternalSession): ExternalResponse
  capabilities(): GatewayCapabilities
}
```

## 17.2 Gateway 类型

```text
Gateway Layer
├── ClipboardGateway
├── ApiGateway
├── MCPGateway
├── BrowserAutomationGateway
└── CloudAgentGateway
```

## 17.3 Clipboard Gateway

```yaml
clipboard_gateway:
  dispatch_mode: "manual"
  supports_streaming: false
  supports_attachments: "manual"
  requires_human_action: true
  audit_level: "full"
```

## 17.4 API Gateway，未来备用

```yaml
api_gateway:
  dispatch_mode: "automatic"
  providers:
    - openai
    - anthropic
    - gemini
    - openrouter
  supports_streaming: true
  supports_structured_output: true
  supports_tool_calling: true
```

## 17.5 MCP Gateway，未来备用

```yaml
mcp_gateway:
  dispatch_mode: "tool_protocol"
  transport:
    - stdio
    - sse
    - http
  message_format: "mcp_message"
  supports_tools: true
```

## 17.6 Browser Automation Gateway，未来备用

```yaml
browser_gateway:
  dispatch_mode: "semi_automatic"
  engines:
    - playwright
    - browser_mcp
    - computer_use
  supports_web_ui: true
  requires_user_login: true
```

---

# 18. External Session

## 18.1 作用

一次对外求助对应一个 External Session。

一个 Case 可以有多个 Session。

例如：

```text
Case
├── Session 1: ChatGPT Web
├── Session 2: Claude Web
└── Session 3: Gemini API
```

## 18.2 Schema

```yaml
external_session:
  id: "session_clipboard_gpt_001"
  case_id: "case_2026_06_30_001"

  gateway: "clipboard"
  provider: "chatgpt_web"
  model_label: "gpt-4.5-or-unknown"

  status: "waiting_response"

  package_id: "pkg_001"
  export_id: "export_001"
  response_ids: []

  started_at: "2026-06-30T11:05:00Z"
  completed_at: null

  human_actions:
    - type: "copied_to_clipboard"
      timestamp: "2026-06-30T11:06:00Z"
    - type: "pasted_to_external_ai"
      timestamp: null
    - type: "pasted_response_back"
      timestamp: null
```

---

# 19. Response Ingestion Pipeline

## 19.1 目标

外部 AI 回复不能作为纯文本保存。

FEOS 必须解析为结构化对象。

## 19.2 Pipeline

```text
Raw Response
    ↓
Format Detection
    ↓
Section Extraction
    ↓
Claim Extraction
    ↓
Recommendation Extraction
    ↓
Risk Extraction
    ↓
Assumption Extraction
    ↓
Patch Extraction
    ↓
Action Extraction
    ↓
Graph Update
    ↓
Verification Queue
```

## 19.3 Parsed Response Schema

```yaml
parsed_response:
  id: "parsed_resp_001"
  response_id: "resp_001"
  case_id: "case_2026_06_30_001"

  summary:
    text: "The MCP adapter likely returns a raw object instead of the required MCP response wrapper."

  root_cause:
    claim: "MCP response adapter misses required result field"
    confidence: 0.86
    supporting_evidence_refs:
      - "ev_stacktrace_001"
      - "ev_toolcall_001"

  recommendations:
    - id: "rec_001"
      type: "code_change"
      description: "Wrap tool result into { result: ... } before returning"
      target_files:
        - "src/mcp/adapter.ts"
      confidence: 0.82
      risk_level: "medium"

  patches:
    - id: "patch_001"
      format: "diff_or_pseudocode"
      content_ref: "responses/patch_001.diff"

  validation_plan:
    commands:
      - "npm test"
      - "npm run test:mcp"
    expected_result: "Schema validation passes"

  risks:
    - id: "risk_001"
      description: "Changing response wrapper may break existing callers"
      mitigation: "Add compatibility test"

  assumptions:
    - id: "asm_001"
      description: "The MCP SDK expects result field at top level"
      needs_verification: true

  follow_up_questions:
    - "Can you show the MCP adapter code?"
```

---

# 20. Verification Layer

## 20.1 强制原则

任何外部建议进入执行前必须验证。

## 20.2 Verification 类型

```yaml
verification_types:
  evidence_alignment:
    description: "建议是否被现有证据支持"

  constraint_check:
    description: "是否违反项目约束"

  architecture_check:
    description: "是否违反架构原则"

  security_check:
    description: "是否引入安全风险"

  compatibility_check:
    description: "是否破坏兼容性"

  dependency_check:
    description: "是否要求不允许的新依赖"

  testability_check:
    description: "是否可测试"

  knowledge_conflict_check:
    description: "是否与历史知识冲突"

  sandbox_check:
    description: "可选，在隔离环境中试运行"
```

## 20.3 Verification Result Schema

```yaml
verification_result:
  id: "ver_001"
  case_id: "case_2026_06_30_001"
  recommendation_id: "rec_001"

  status: "passed_with_warnings" # passed | failed | passed_with_warnings | needs_human_review

  checks:
    evidence_alignment:
      status: "passed"
      notes: "Recommendation matches stack trace and tool call evidence."

    constraint_check:
      status: "passed"

    architecture_check:
      status: "passed_with_warnings"
      notes: "Need ensure adapter boundary remains clean."

    security_check:
      status: "passed"

    compatibility_check:
      status: "needs_test"
      notes: "Existing callers may rely on raw object."

  risk_level: "medium"

  required_human_approval: true

  suggested_next_step: "generate_execution_plan"
```

---

# 21. Execution Planning

## 21.1 作用

把经过验证的建议转成可执行计划。

## 21.2 Execution Plan Schema

```yaml
execution_plan:
  id: "plan_001"
  case_id: "case_2026_06_30_001"

  source:
    response_id: "resp_001"
    recommendation_ids:
      - "rec_001"

  status: "pending_approval"

  objective: "Fix MCP response schema validation error"

  steps:
    - id: "step_001"
      type: "inspect"
      description: "Inspect MCP adapter return shape"
      target_files:
        - "src/mcp/adapter.ts"

    - id: "step_002"
      type: "edit"
      description: "Wrap returned payload with result field"
      target_files:
        - "src/mcp/adapter.ts"

    - id: "step_003"
      type: "test"
      description: "Run MCP schema validation tests"
      commands:
        - "npm run test:mcp"

    - id: "step_004"
      type: "regression_test"
      commands:
        - "npm test"

  rollback:
    strategy: "git_checkout_or_reverse_patch"
    files:
      - "src/mcp/adapter.ts"

  approval:
    required: true
    approved_by: null
```

---

# 22. Execution Tracking

## 22.1 Timeline

所有执行动作进入 Case Timeline。

```yaml
timeline_event:
  id: "evt_001"
  case_id: "case_2026_06_30_001"
  timestamp: "2026-06-30T12:00:00Z"

  type: "execution_step_completed"
  actor: "local_agent"

  payload:
    step_id: "step_002"
    result: "success"
    files_changed:
      - "src/mcp/adapter.ts"
```

## 22.2 Outcome Schema

```yaml
outcome:
  case_id: "case_2026_06_30_001"
  status: "resolved"

  resolution:
    root_cause: "MCP adapter returned unwrapped tool result"
    fix_summary: "Wrapped tool response in { result: payload }"
    files_changed:
      - "src/mcp/adapter.ts"
      - "tests/mcp/adapter.test.ts"

  validation:
    commands_run:
      - command: "npm run test:mcp"
        status: "passed"
      - command: "npm test"
        status: "passed"

  confidence: 0.93

  external_contribution:
    response_id: "resp_001"
    useful: true
    adopted_recommendations:
      - "rec_001"
```

---

# 23. Knowledge Distillation Layer

## 23.1 原则

不直接保存 GPT 回复。

FEOS 必须从 Case 中蒸馏可复用知识。

## 23.2 Knowledge 类型

```yaml
knowledge_types:
  failure_pattern:
    description: "某类失败的识别模式"

  resolution_pattern:
    description: "某类问题的解决模式"

  anti_pattern:
    description: "被证明无效或危险的做法"

  playbook:
    description: "可执行排查或修复流程"

  decision_rule:
    description: "未来类似场景下的判断规则"

  architecture_note:
    description: "架构层面的经验"

  tool_specific_note:
    description: "特定工具、MCP、框架的经验"
```

## 23.3 Knowledge Candidate Schema

```yaml
knowledge_candidate:
  id: "kc_001"
  case_id: "case_2026_06_30_001"

  type: "failure_pattern"

  title: "MCP tool response missing result wrapper"

  content:
    when:
      - "MCP tool call fails with schema validation"
      - "Error mentions missing result field"
    likely_cause:
      - "Tool adapter returns raw payload instead of MCP response envelope"
    recommended_action:
      - "Inspect adapter boundary"
      - "Wrap response as { result: payload }"
    avoid:
      - "Do not change tool business logic before checking adapter schema"

  applicability:
    project_types:
      - "MCP-based agent system"
    versions:
      - "MCP SDK >= 1.8"
    confidence: 0.88

  evidence:
    source_case: "case_2026_06_30_001"
    supporting_evidence:
      - "ev_stacktrace_001"
      - "outcome_001"

  lifecycle:
    status: "captured"
    verified: false
    reuse_count: 0
    deprecated: false
```

## 23.4 Knowledge Lifecycle

```text
Captured
  ↓
Verified
  ↓
Indexed
  ↓
Retrieved
  ↓
Reused
  ↓
Updated / Deprecated
  ↓
Archived
```

---

# 24. Knowledge OS 集成

## 24.1 写入对象

```text
Knowledge OS
├── Semantic Memory
│   └── 工程事实、框架规则、协议约束
│
├── Episodic Memory
│   └── 完整 Case 经验
│
├── Procedural Memory
│   └── Playbook、修复流程、排查步骤
│
├── Pattern Library
│   ├── Failure Pattern
│   ├── Resolution Pattern
│   ├── Architecture Pattern
│   ├── Decision Pattern
│   └── Anti-pattern
│
└── Policy Memory
    └── 未来不应违反的约束和规则
```

## 24.2 写入规则

知识写入必须包含：

- 来源 Case
- 证据引用
- 适用条件
- 反例
- 成功状态
- 版本范围
- 置信度
- 失效条件
- 最近验证时间

---

# 25. 文件系统布局

建议本地存储结构如下：

```text
.forge/
└── feos/
    ├── cases/
    │   └── case_2026_06_30_001/
    │       ├── case.yaml
    │       ├── timeline.jsonl
    │       ├── graph.json
    │       ├── evidence/
    │       │   ├── index.yaml
    │       │   ├── raw/
    │       │   │   ├── ev_stacktrace_001.txt
    │       │   │   ├── ev_toolcall_001.json
    │       │   │   └── ev_diff_001.patch
    │       │   └── normalized/
    │       │       ├── ev_stacktrace_001.yaml
    │       │       └── ev_toolcall_001.yaml
    │       ├── context/
    │       │   ├── ctxpkg_001.yaml
    │       │   └── ctxpkg_001.rendered.md
    │       ├── exports/
    │       │   ├── clipboard.md
    │       │   ├── package.json
    │       │   ├── manifest.json
    │       │   ├── redaction_report.json
    │       │   ├── evidence_index.md
    │       │   └── attachments/
    │       ├── sessions/
    │       │   └── session_clipboard_gpt_001.yaml
    │       ├── responses/
    │       │   ├── resp_001_raw.md
    │       │   └── resp_001_parsed.yaml
    │       ├── verification/
    │       │   └── ver_001.yaml
    │       ├── execution/
    │       │   ├── plan_001.yaml
    │       │   └── outcome.yaml
    │       └── knowledge/
    │           ├── candidates.yaml
    │           └── distilled.yaml
    │
    ├── policies/
    │   ├── default.yaml
    │   ├── redaction.yaml
    │   └── gateway.yaml
    │
    ├── renderer_profiles/
    │   ├── gpt_markdown_debug.yaml
    │   ├── claude_markdown_architecture.yaml
    │   └── generic_markdown.yaml
    │
    ├── knowledge_index/
    └── metrics/
```

---

# 26. CLI / API 设计

## 26.1 CLI 命令

```bash
# 创建 Case
forge feos create --from-task task_abc123

# 自动采集证据
forge feos collect case_001

# 构建 Graph
forge feos graph build case_001

# 检索相似案例
forge feos retrieve similar case_001

# 生成假设
forge feos hypothesis generate case_001

# 编译上下文
forge feos context compile case_001 --target chatgpt_web --budget 24000

# 导出 Clipboard Artifact
forge feos export case_001 --gateway clipboard --provider chatgpt_web

# 复制到剪贴板
forge feos clipboard copy case_001

# 导入外部回复
forge feos import response case_001 --from-clipboard

# 解析回复
forge feos response parse case_001 --response resp_001

# 验证建议
forge feos verify case_001

# 生成执行计划
forge feos plan case_001

# 执行计划
forge feos execute case_001 --plan plan_001

# 记录结果
forge feos outcome evaluate case_001

# 蒸馏知识
forge feos distill case_001

# 归档
forge feos archive case_001
```

## 26.2 内部 API

```typescript
interface FEOS {
  createCase(input: CreateCaseInput): EscalationCase
  collectEvidence(caseId: string): EvidenceCollectionResult
  buildGraph(caseId: string): CaseGraph
  retrieveSimilar(caseId: string): SimilarityResult[]
  generateHypotheses(caseId: string): Hypothesis[]
  checkPolicy(caseId: string, packageId?: string): PolicyResult
  compileContext(input: CompileContextInput): ContextPackage
  buildPackage(input: BuildPackageInput): EscalationPackage
  exportPackage(input: ExportPackageInput): ExportResult
  importResponse(input: ImportResponseInput): ExternalResponse
  parseResponse(responseId: string): ParsedResponse
  verify(caseId: string): VerificationResult[]
  createExecutionPlan(caseId: string): ExecutionPlan
  recordOutcome(caseId: string, outcome: Outcome): void
  distillKnowledge(caseId: string): KnowledgeCandidate[]
}
```

---

# 27. Observability

## 27.1 必须记录的指标

```yaml
metrics:
  case:
    - cases_created_total
    - cases_resolved_total
    - cases_unresolved_total
    - average_case_duration
    - average_time_to_external_response
    - average_time_to_resolution

  escalation:
    - escalation_trigger_count
    - false_escalation_rate
    - avoided_escalation_by_similarity_retrieval
    - external_rounds_per_case

  context:
    - context_tokens_estimated
    - compression_ratio
    - evidence_coverage_rate
    - omitted_high_value_evidence_count

  gateway:
    - clipboard_exports_total
    - clipboard_imports_total
    - api_exports_total
    - mcp_exports_total
    - provider_success_rate

  verification:
    - recommendations_parsed_total
    - recommendations_passed_verification
    - recommendations_rejected
    - high_risk_recommendations

  knowledge:
    - knowledge_candidates_created
    - knowledge_items_verified
    - knowledge_reuse_count
    - knowledge_deprecated_count
```

---

# 28. Security & Audit

## 28.1 外发前强制检查

任何 Gateway 外发前都必须：

1. 执行 Secret Scan
2. 执行 PII Scan
3. 执行 Internal Path Redaction
4. 执行 License Policy Check
5. 生成 Redaction Report
6. 生成 Export Audit Record
7. 要求用户确认

## 28.2 Audit Record

```yaml
export_audit:
  export_id: "export_001"
  case_id: "case_2026_06_30_001"
  gateway: "clipboard"
  provider: "chatgpt_web"

  exported_at: "2026-06-30T11:06:00Z"
  exported_by: "human"

  content_hash: "sha256:exported..."
  redacted: true

  redaction_report:
    secrets_removed: 2
    pii_removed: 0
    internal_paths_redacted: 4

  user_confirmed: true
```

---

# 29. MVP 实施优先级

## Phase 1：必须先做

目标：把人工求助流程标准化、资产化、闭环化。

必须实现：

1. Escalation Case
2. Case 状态机
3. Evidence Collection 基础版
4. Evidence Schema
5. Case Graph 简化版
6. Context Compiler 基础版
7. Markdown Renderer
8. Clipboard Gateway
9. Clipboard Export
10. Clipboard Import
11. Response 保存
12. Response 基础解析
13. Verification 基础版
14. Execution Plan 基础版
15. Outcome 记录
16. Knowledge Candidate 写入

Phase 1 最重要产物：

```text
可以稳定完成：
发现问题 → 自动整理证据 → 生成可粘贴 GPT/Claude 的高质量 Artifact → 导入回复 → 解析建议 → 验证 → 执行 → 沉淀知识
```

## Phase 2：增强智能性

加入：

1. Hypothesis Manager
2. Similarity Retrieval
3. Policy Plane 完整版
4. Redaction 完整版
5. Observability
6. Knowledge Lifecycle
7. Renderer Profiles 多模型优化

## Phase 3：接入未来 Gateway

加入：

1. API Gateway
2. MCP Gateway
3. Browser Automation Gateway
4. 多模型 Session 管理
5. 多轮 External Reasoning
6. Structured Output Parsing
7. Sandbox Verification

## Phase 4：自演化

加入：

1. 多 Agent Investigation
2. Adaptive Escalation Router
3. Context Compiler 自动优化
4. Procedure Learning
5. Skill Library
6. Knowledge Reuse Feedback
7. 自动生成项目级 Debug Playbook

---

# 30. 最终推荐版本总结

最终版 FEOS 应该被定义为：

> **FORGE Factory 的案例智能操作系统。**

它的核心不是 Prompt，不是 HELP_REQUEST.md，也不是 GPT 对话。  
它的核心是：

```text
Escalation Case
    +
Case Graph
    +
Context Compiler
    +
Gateway Layer
    +
Verification Layer
    +
Knowledge Lifecycle
```

当前阶段，主流程必须是：

```text
FEOS 生成 Artifact
    ↓
用户复制 clipboard.md
    ↓
用户粘贴到 GPT / Claude 网页
    ↓
用户复制外部回复
    ↓
用户粘贴回 FEOS
    ↓
FEOS 解析、验证、执行、沉淀
```

未来阶段，同一个 Escalation Package 可以无缝发往：

```text
API Gateway
MCP Gateway
Browser Automation Gateway
Cloud Agent Gateway
```

而不需要修改核心 Case、Evidence、Graph、Context、Knowledge 体系。

---

# 31. 一句话最终架构

**FEOS = Event-sourced Escalation Case + Evidence-backed Case Graph + Token-aware Context Compiler + Clipboard-first Gateway Layer + Verification-gated Execution + Knowledge Distillation Loop。**

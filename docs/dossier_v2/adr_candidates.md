<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间）：2026-06-20 22:30:00 CST
-->

# ADR Candidates – 缺失但关键的架构决策

> 为下一任架构师补录的 ADR 候选清单。均基于当前代码逆向推断，需正式评审后转正。

---

## ADR-C001: Smart Proxy 健康探针与熔断策略

- **Status**: Proposed
- **Context**: Smart Proxy 是全厂唯一入口，无 /healthz、无熔断、无重试。上游模型崩溃直接 5xx 透传。2026-06-20 成功 case 耗时 1132s，无超时分级。
- **Decision**: 
  - 新增 GET /healthz 返回各后端模型存活状态
  - chat_proxy 增加 upstream 重试 2 次，指数退避
  - 引入 circuit breaker – 连续 3 次失败熔断 60s
  - chunk 超时从固定 600s 改为 per-model 可配置
- **Alternatives**: 
  - 直接用 Envoy / Traefik 做 L7 网关 – 引入额外运维复杂度，VRAM 调度仍需自研
  - 不做熔断靠人工重启 – 现状，已导致多次卡顿
- **Consequences**: 
  - + 可用性提升
  - - 增加网关复杂度 ~200 LOC
  - - 需补回归测试
- **Evidence**: `_infra/smart_proxy_streaming.py:112`, `risk_register.csv R-001`
- **Why this matters for upgrade**: 网关是承重墙，不加固就扩容等于放大单点故障。

---

## ADR-C002: LLM Backend 测试替身与录制回放

- **Status**: Proposed
- **Context**: llm_client 强依赖真实模型，无 fake / mock，导致测试覆盖 <15%，CI 无法跑。
- **Decision**:
  - 为 LLMBackend 增加 `FakeBackend` – 返回固定/录制响应
  - 引入 VCR.py / pytest-recording – 首次真跑录制，后续回放
  - CI 默认使用 FakeBackend，nightly 跑真实模型冒烟
- **Alternatives**:
  - 全部 mock – 失去集成信心
  - 每次 CI 拉真模型 – 成本/时间不可接受
- **Consequences**:
  - + 测试覆盖可快速提升至 60%+
  - + 重构信心提升
  - - 需维护录制文件
- **Evidence**: `risk_register.csv R-009`, `evidence_index.csv E-022`
- **Why this matters**: 没有测试护栏，任何架构升级都是盲改。

---

## ADR-C003: 配置统一与继承机制

- **Status**: Proposed
- **Context**: `config/models.yaml` 在根目录与 `projects/debt-collection/config/`, `projects/legal-bot/config/` 等多处重复拷贝，无同步机制，已观察到漂移风险。
- **Decision**:
  - 根 `config/` 为全局 SSOT
  - 项目级 config 允许 overlay – 仅覆盖差异字段，未指定则继承全局
  - `load_all_configs()` 增加版本校验 – project_config_version 必须兼容 factory_config_version
  - CI 增加 `forge config-lint` – 检测漂移
- **Alternatives**:
  - 强制 symlink – 简单但不支持项目个性化
  - 各项目完全独立 – 现状，导致漂移
- **Consequences**:
  - + 消灭配置漂移
  - + 支持项目个性化
  - - loader 复杂度增加
- **Evidence**: `risk_register.csv R-006`, `evidence_index.csv E-033`
- **Why**: 配置是三文件 SSOT 核心契约，漂移 = 运行时崩溃。

---

## ADR-C004: 容器化交付标准

- **Status**: Proposed
- **Context**: 当前部署为 Mac 手工启动，无 Dockerfile，无 compose，无法在 Linux/CI 复现。
- **Decision**:
  - 提供 `Dockerfile.peer-review` + `Dockerfile.smart-proxy` + `docker-compose.yml`
  - 模型服务器仍为外部依赖 – 通过 `MODEL_BASE_URL` 注入
  - 提供 `docker-compose.local.yml` – 挂载本地 Ollama
  - CI 构建镜像并推送 ghcr.io
- **Alternatives**:
  - 继续裸机 – 无法扩展/复现
  - 全量容器化含模型 – 镜像过大（>30GB），不现实
- **Consequences**:
  - + 可移植性大幅提升
  - + CI 可集成测试
  - - Mac Metal 加速在容器内需额外配置
- **Evidence**: `risk_register.csv R-016`, `evidence_index.csv E-034`
- **Why**: 不容器化就无法上云、无法多租户。

---

## ADR-C005: 可观测性基线 – OpenTelemetry

- **Status**: Proposed
- **Context**: 仅有简易 logger，无 trace，无 metrics，1132s 慢请求无法定位瓶颈在哪个 node。
- **Decision**:
  - 引入 opentelemetry-sdk – 为每个 LangGraph node 创建 span
  - 导出至 OTLP – 本地可用 Jaeger / Langfuse
  - 关键 metrics: node_latency_seconds, llm_tokens_in/out, vram_used_gb, divergence_score
  - 日志结构化 JSON (structlog)
- **Alternatives**:
  - 继续 print log – 无法分布式追踪
  - 自研 trace – 重复造轮子
- **Consequences**:
  - + 故障定位时间从小时降至分钟
  - + 为性能优化提供数据
  - - 增加依赖体积
- **Evidence**: `risk_register.csv R-013`, `evidence_index.csv E-035`
- **Why**: 无观测的升级 = 盲人摸象。

---

## ADR-C006: 密钥管理 – 从 .env 明文到 Vault / 1Password

- **Status**: Proposed
- **Context**: API Key 明文存于 `_infra/.env`，无加密，无轮转，无审计。
- **Decision**:
  - 开发环境: 1Password CLI `op run --env-file=.env.tpl --`
  - CI/CD: GitHub Actions Secrets
  - 生产 (未来): HashiCorp Vault / AWS Secrets Manager
  - `config/schemas.py` 的 `${ENV_VAR}` 解析保持兼容
  - 增加启动时密钥存在性校验，缺失则 fail-fast
- **Consequences**:
  - + 消除密钥泄露风险
  - - 本地开发需安装 op CLI
- **Evidence**: `risk_register.csv R-007`, `evidence_index.csv E-031`
- **Why**: 安全基线是对外发布的前提。

---

## ADR-C007: ModelLauncher 抽象 – 解耦 AppleScript 平台绑定

- **Status**: Proposed
- **Context**: `ensure_server()` 硬编码 AppleScript 拉起 MTPLX，仅 Mac 可用，阻碍 Linux/云部署。
- **Decision**:
  - 定义 `ModelLauncher` 接口: `start(model_cfg) -> bool`, `stop()`, `is_alive() -> bool`, `vram_used() -> int`
  - 实现: `AppleScriptLauncher(Mac)`, `SystemdLauncher(Linux)`, `DockerLauncher`, `KubernetesLauncher`
  - 通过 `MODEL_LAUNCHER=applescript|systemd|docker` 环境变量切换
  - Smart Proxy 仅依赖接口，不感知平台
- **Consequences**:
  - + 可移植性从 Mac-only 提升至跨平台
  - + 为 K8s 扩展铺路
  - - 增加抽象层复杂度
- **Evidence**: `risk_register.csv R-014`, `evidence_index.csv E-020`
- **Why**: 不解耦平台绑定，就无法走出 Mac 单机。

---

> 以上 7 个 ADR Candidate 建议按 C002 → C003 → C001 → C005 → C006 → C004 → C007 顺序落地（测试护栏 → 配置收敛 → 网关加固 → 可观测 → 安全 → 容器化 → 平台抽象）。
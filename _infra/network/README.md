<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-06-22 20:58:00
-->

# FORGE Network（联网功能增量子模块）

**位置**：`_infra/network/`（现有 FORGE Factory 的**增量模块**）

本模块为 FORGE Factory 叠加：
- 本地公开搜索（SearXNG）
- 网页提取（Crawl4AI + 降级）
- 输入净化 + Privacy Gateway（7 层）
- MCP 安全治理 + 模式隔离
- 浏览器自动化（后续 Phase）
- 本地 RAG

**严格原则**：
- 复用现有 FORGE 架构（根 pyproject、config/、runtime/、forge CLI）
- 不创建独立 pyproject / 独立顶级 src
- 所有代码放在本目录下
- 配置统一使用根 `config/network.yaml`

更多详情见根目录 `NETWORK_ARCHITECTURE_FINAL.md` 和 `NETWORK_ENGINEERING_DESIGN.md`（已按增量模式调整）。

## 快速开发命令
```bash
# 查看 network 配置加载状态
python -m _infra.network.cli config

# 运行 health 检查（外部服务未启动时可能显示 degraded）
python -m _infra.network.cli health

# 运行 network 单元测试
python -m pytest _infra/network/tests/unit/ -q
```

## 当前阶段（2026-06-22）

已完成：
- E1 基础设施核心（config_loader / exceptions / logger / secrets / audit_log / health_check）
- E3 搜索核心（SearXNGProvider / URL normalizer / domain scorer / SearchCache）
- E4 提取核心（Crawl4AIProvider / trafilatura fallback / Markdown cleaner / ExtractorChain）
- E5-C1 / E5-C2（InputSanitizer + Unicode normalize）
- E5-C3-S1-T1/T2/T3/T4（PIIDetector ABC / PresidioDetector / 中文 recognizers / Token & API Key recognizers；Presidio 相关测试在未安装 `presidio_analyzer` 时依赖门控跳过）
- E5-C4-S1-T1（SpaCyNERDetector + spaCy 模型下载脚本；单元测试通过依赖注入 fake NLP，避免强制下载模型）
- E5-C5-S1-T1（QwenPIIClassifier；Ollama lazy import + fake client 单元测试，失败降级为 uncertain）
- E5-C6-S1-T1（PIIReplacer；占位符替换 + mapping_id + in-process queryable mapping store）
- E5-C6-S1-T2（PII Map DB；SQLCipher driver 优先 + sqlite3 field-level AES-256 fallback，错误密钥无法解密 original）
- E5-C7-S1-T1（JSON Schema 输出验证；禁止 raw PII value 出现在输出 entities 中）
- E5-C8-S1-T1（CanaryTokenMonitor；配置驱动 canary token，命中立即阻断 + masked audit metadata）

当前下一候选任务：`TASK_BACKLOG.md` 中的 E5-C9-S1-T1 — PrivacyGateway 主管线。

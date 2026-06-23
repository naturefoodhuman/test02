<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-23 14:24:45
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
- E5-C9-S1-T1/T2（PrivacyGateway 主管线 + build_privacy_gateway 工厂函数；L1-L7 组装，支持 light/full mode 与 config-driven 一行构建）
- E11-C2-S1-T1（Prompt Injection 安全测试；恶意 HTML fixtures + Unicode/URL 编码/隐藏指令/tool-call trigger 覆盖）
- E11-C4-S1-T1（PII 绕过安全测试；Unicode/零宽/Base64/URL encoding/表格/JSON/code variable 覆盖）
- E11-C6-S1-T1（Canary Token 端到端测试；search/extract/browser/privacy output 任一位置命中立即阻断）
- E2-C1-S1-T1（MCP Server 安装脚本；pinned git clone + exact commit checkout + mcp-scan admission + lockfile）
- E2-C2-S1-T1（mcp-scan 集成；scanner parser + scan scripts + lockfile local_path 扫描）
- E2-C3-S1-T1（MCP Schema Hash 校验；canonical hash + lockfile pin + schema change audit）
- E2-C4-S1-T1（MCP Guard 核心抽象；tool call/result/decision models + check 接口 + audit + schema guard）
- E2-C4-S1-T2（模式权限策略；coding/research/private 配置驱动 server/tool 边界）
- E2-C4-S1-T3（高危工具人工审批流；严格 yes 单次审批 + audit）
- E2-C4-S1-T4（参数安全验证；危险 JS/cookie/storage/URL/长度/PII/secret 拦截）
- E11-C5-S1-T1（Cookie 泄露测试；MCP args + output layer cookie/session 拦截）
- E6-C1-S1-T1（Coding MCP profile；`.mcp.json.coding` JSON 合法且不引用 browser/search/private servers）
- E3-C1-S1-T1/T2（SearXNG Docker Compose + settings；本地 127.0.0.1:8080 + JSON format）
- E4-C1-S1-T1（Crawl4AI Docker Compose service；本地 127.0.0.1:11235）
- E6-C1-S1-T2（Research MCP profile；searxng/crawl4ai/playwright-public，本地端点 + pinned paths）

当前下一候选任务：`TASK_BACKLOG.md` 中 M7 E8-C1-S1-T1 — Chrome DevTools MCP 安装（用于解锁 E6-C1-S1-T3 Private profile 前置依赖），或按用户指定继续其他任务。

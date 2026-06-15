<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间：2026-06-15 03:10:00 CST
-->

# HANDOFF —— 接力交接文档（v2.0 第28轮修订版）

> 目标：任何 Agent 5 分钟内接手并继续开发。
> ⚠️ **任何 Agent 接手后，必须先读本文档，再读 docs/PROJECT_STATE.md，然后看 docs/DEV_LOG.md 最后一轮记录。**

---

## 1. 项目定位
本产品为 **AI 项目孵化工厂 (FORGE Factory)**。
试点项目 `debt-collection` 是用来压测工厂能力的"沙包"，不作为正式开发目标。

**当前架构版本**：v1.1.0（LangGraph 迁移已启动，双文件体系 + DataPrivacyGate 已落地）

---

## 2. 运行环境与路径

### 老板真机路径
- **macOS 绝对路径：** `/Users/naturist/MusicProject/AI-Project-Incubation-Factory`
- **沙箱开发路径：** `/home/user/test02`（Agent 开发用，老板不用管）
- **GitHub 仓库：** `https://github.com/naturefoodhuman/test02.git`

### 同步方式
- Agent 改完后生成 ZIP 补丁 → 老板 `unzip -o patch_xxx.zip` 覆盖
- 或者老板 `git pull` 拉取最新代码
- **标准化发布流程**：`make release` 或 `bash release.sh [patch|minor|major] "发布说明"` → 自动更新版本号、CHANGELOG、git tag → `git push origin main --tags`

### 虚拟环境 (Venv) 矩阵
| 环境 | 路径 | 用途 |
|------|------|------|
| 主工厂环境 | `.venv`（根目录） | 运行网关 (start-litellm.sh)、专家咨询、peer-review |
| MinerU 专用 | `projects/debt-collection/runtime/mineru_env` | PDF 深度解析 |
| forge CLI | `_infra/forge_tools/` 下独立安装 | 五阶段状态机 |

### 模型矩阵 (Ollama / 中国 API)
| 模型别名 | 来源 | 用途 |
|----------|------|------|
| `local-qwen35b` | Ollama `qwen3.5:35b-a3b-q8_0` | 本地执行核心（默认主专家） |
| `local-deepseek-r1` | Ollama `deepseek-r1:32b` | 本地推理核心 |
| `local-coder` | Ollama `qwen2.5-coder:32b` | 本地代码任务 |
| `local-fast` | Ollama `qwen2.5:7b` | 快速分类/路由 |
| `embedding` | Ollama `bge-m3` | 向量检索 |
| `deepseek-flash` | DeepSeek API | 外源快速评审 |
| `deepseek-pro` | DeepSeek API | 外源高质量汇总 |
| `qwen-plus` | Alibaba API | 超长上下文/中文法律 |
| `glm-5` | Zhipu API | 中文专项 |

> 完整配置见 `config/models.yaml`（A 文件）。节点如何调用见 `config/routing_plans.yaml`（B 文件），切换方案只改 `active_plan` 字段。

---

## 3. 核心规则（Agent 必须遵守）

### R1 — 老板说的算
- 老板拍板的决策（见 `docs/DECISIONS.md`）**不得擅自推翻**，要改必须先问老板。

### R2 — 反方评估（穷尽调研）
- 决策前必须调研业界主流方案，给出优劣对比表。
- 调研原则：**穷尽全世界相关项目** → 正方分析（优点/可借鉴） → 反方分析（缺点/不适用） → 给出推荐方案 → **等老板认可后再执行**。
- 老板说"没用或不适合的项目不能随便拉取下来用，只用最好最适合的"。

### R3 — 保姆级指示
- 给老板的每条操作指令必须包含 **四要素**：
  1. **终端编号**（终端 A / 终端 B / …）
  2. **当前路径**（`cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory`）
  3. **虚拟环境状态**（`source .venv/bin/activate` 或说明不需激活）
  4. **预期输出**（终端会打印什么，成功/失败的标志）
- **禁止** 给模糊指令如"你试试看""跑一下"。

### R4 — 每轮打包补丁
- 每次改动文件后，必须在 `_patches/` 目录产出 `patch_YYYYMMDD_HHMMSS_<主题>.zip`。
- zip 内路径对齐项目根目录，老板直接 `unzip -o` 覆盖即可。

### R5 — 文件头规范
- 所有新建/修改的文件**必须**在头部注明：
  ```
  # 创建/修改该文件的LLM大模型：XXX
  # 创建时间（北京时间）：YYYY-MM-DD HH:MM:SS
  ```
- Python 文件用 `#` 注释，Markdown 用 `<!-- -->` 注释，YAML 用 `#` 注释。
- ⚠️ **禁止** 在 `.py` 或 `.yaml` 文件用 HTML 注释（`<!-- -->` 会导致 SyntaxError/YAML 解析失败）。

### R6 — 文档同步
- 改了什么模块 → 同步更新 `docs/PROJECT_STATE.md`、`docs/DEV_LOG.md`、`docs/DECISIONS.md`。
- 如果 HANDOFF.md 里的操作 SOP 过时了 → **直接修正 HANDOFF.md**，不要等老板提醒。

---

## 4. 操作 SOP（保姆级）

### 启动 Ollama 服务（终端 A）
```
终端 A:
1. ollama serve
   → 预期输出：ollama listening on :11434
```

### 启动 LiteLLM 网关（终端 B，仅云端模型需要）
```
终端 B:
1. cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
2. source .venv/bin/activate
3. bash _infra/start-litellm.sh
   → 预期输出：📥 加载环境变量 → ✅ GLM_API_KEY 已加载 → 🚀 启动 LiteLLM
```

### 运行 Peer-Review 评审（终端 C）
```
终端 C:
1. cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
2. source .venv/bin/activate
3. 
4. debt review 1
   > **注意**：v1.1.0+ 已迁移到 LangGraph，`debt review` 默认使用 config/routing_plans.yaml 中的 active_plan。
   > 如需临时切换方案：debt review 1 --plan high-quality
   > 使用 API 模型时，若含 human_approve 字段会强制要求输入 yes 确认；local_only 字段会被阻断。
   → 预期输出：
     🔍 启动 Peer-Review 模块 (LangGraph)...
     ✅ peer_review 模块加载成功
     🚀 激活方案: default
     → 主专家完成
     → reviewer_1 完成
     → reviewer_2 完成
     → reviewer_3 完成
     → 汇总完成 (分歧度: 0.00)
     （主专家分析 + 最终汇总结论）
     📝 已记录运行到 MemoryStore：方案 default | 耗时 Xs | 分歧度 0.00
```

### 运行隐私安全模式（全部本地，无数据出境）
```
终端 C:
1. debt review 1 --plan all-local
   → 预期输出：使用 all-local 方案，数据完全不出本地，不触发确认门
```

### 录入测试债务
```
终端 C:
debt add "张三" 50000 --evidence "微信转账"
→ 预期输出：✅ 已录入债务 #1：张三 50000.0元
```

---

## 5. 项目目录结构（快速索引）

```
AI-Project-Incubation-Factory/
├── HANDOFF.md                      # ⭐ 本文档（交接必读）
├── README.md                       # 项目总览
├── docs/
│   ├── PROJECT_STATE.md            # 当前进度快照
│   ├── DECISIONS.md                # 已拍板决策（不得擅自改）
│   └── DEV_LOG.md                  # 逐轮开发日志
├── _infra/                         # 基础设施（LiteLLM 网关、自检脚本）
├── _factory/
│   ├── skills/                     # SKILL.md 技能库
│   │   ├── prescription-risk.skill.md
│   │   ├── asset-search.skill.md
│   │   └── compliance-layered.skill.md
│   ├── patterns/
│   │   ├── peer-review/            # FB-14 多专家评审（v1.1.0 LangGraph）
│   │   │   ├── src/peer_review/
│   │   │   │   ├── graph/          # LangGraph 图结构
│   │   │   │   │   ├── review_graph.py
│   │   │   │   │   ├── nodes/
│   │   │   │   │   │   ├── primary_expert.py
│   │   │   │   │   │   ├── reviewer.py
│   │   │   │   │   │   └── consensus.py
│   │   │   │   │   └── checkpointer.py
│   │   │   │   ├── platform/       # 平台层（路由/隐私/记忆/知识/决策）
│   │   │   │   │   ├── routing_plan_engine.py
│   │   │   │   │   ├── data_privacy_gate.py
│   │   │   │   │   ├── memory_store.py
│   │   │   │   │   ├── knowledge_hub.py
│   │   │   │   │   └── decision_engine.py
│   │   │   │   ├── config/         # Pydantic 配置层
│   │   │   │   │   ├── schemas.py
│   │   │   │   │   └── loader.py
│   │   │   │   ├── orchestrator.py # LangGraph 兼容入口（保留 Agno 旧入口）
│   │   │   │   └── llm_client.py
│   │   │   └── tests/
│   │   │       ├── test_peer_review_langgraph.py
│   │   │       └── verify_architecture.py
│   │   ├── expert-consultant/
│   │   ├── ingestion-pipeline/
│   │   ├── data-acquisition/
│   │   └── llm-telemetry/
│   └── experts/
│       ├── debt-lawyer.expert/     # 主专家
│       ├── risk-assessor.expert/   # 评审专家
│       ├── compliance-auditor.expert/
│       └── execution-strategist.expert/
├── _patches/                       # 补丁包目录
├── projects/
│   ├── _TEMPLATE/                  # 新项目脚手架
│   └── debt-collection/            # 试点项目
│       ├── src/debt/               # 债务助手核心代码
│       │   ├── cli.py              # CLI 入口（含 review 命令）
│       │   ├── models.py
│       │   └── strategy.py
│       └── tests/
└── _patches/
```

---

## 6. 常见排障

| 现象 | 原因 | 解决方案 |
|------|------|---------|
| `OPENAI_API_KEY not set` | Team 未指定本地模型，默认走 OpenAI | 确保 `orchestrator.py` 中 Team 传入了 `model=Ollama(id=...)` |
| `ModuleNotFoundError: No module named 'agno'` | 依赖未安装 | `uv pip install agno llama-index-core chromadb` |
| `f-string expression part can include a backslash` | Python 3.11 语法限制 | f-string 花括号内不能有 `\n` 等转义字符，改用变量拼接 |
| `ModuleNotFoundError: No module named 'debt'` | PYTHONPATH 未设置 | `export PYTHONPATH=$PYTHONPATH:$(pwd)/projects/debt-collection/src` |
| `cannot import name 'Mode' from 'agno.team.mode'` | Agno 2.6 API 变更 | `mode="sequential"` 替换 `mode=Mode.SEQUENTIAL` |
| `Agent.__init__() got an unexpected keyword argument 'add_history_to_messages'` | Agno 参数废弃 | 移除 `add_history_to_messages` 和 `markdown` 参数 |
| 日志显示 `正在构建专家  向量索引`（ID 为空） | YAML 缺 `id` 字段 | 在专家 YAML 第一行加 `id: xxx` |
| `debt review` 输出 "模型调用不可用" | LiteLLM 网关和 Ollama 都未启动 | 终端 A 启动 `ollama serve`，终端 B 启动 `bash _infra/start-litellm.sh` |
| `InvalidUpdateError: Can receive only one value per step` | 旧版测试或旧代码未使用 LangGraph `Annotated` reducer | 确保使用 `test_peer_review_langgraph.py` 新测试，旧版已删除 |
| `ModuleNotFoundError: No module named 'langgraph'` | 依赖未安装 | `pip install langgraph>=1.0.10 langgraph-checkpoint-sqlite>=3.0.1` |

---

## 7. 给接手 Agent 的检查清单

接手后按顺序执行：
- [ ] 读本文档（HANDOFF.md）
- [ ] 读 `docs/PROJECT_STATE.md` 了解当前进度
- [ ] 读 `docs/DECISIONS.md` 了解已拍板决策（不得擅自改）
- [ ] 读 `docs/DEV_LOG.md` 最后一轮了解最近做了什么
- [ ] 确认老板的下一个需求是什么（如果老板没说，主动问）
- [ ] **任何新功能/架构变更前，先做 R2 调研**（穷尽→正反评估→老板认可→执行）
- [ ] 改完文件后同步更新所有相关文档
- [ ] 打包 zip 补丁到 `_patches/` 目录
- [ ] 运行对应测试确保通过
- [ ] 给老板保姆级操作指令（终端号/路径/环境/预期输出）

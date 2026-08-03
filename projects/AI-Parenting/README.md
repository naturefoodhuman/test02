<!--
创建/修改该文件的LLM大模型：Claude Opus 4.8
创建时间（北京时间）：2026-08-02 00:00:00
-->

# AI Parenting Copilot

> 家庭私有化 AI 育儿副驾驶系统 —— FORGE Factory 孵化项目。
> 本地优先（local-first）：主控与权威数据在家庭局域网内 Mac，离线可完整记录，不丢记录。

---

## 1. 这是什么

AI Parenting Copilot 是一套部署在家庭 Mac 上的私有化育儿辅助系统，覆盖：

- **记录**：喂奶 / 尿布 / 体温 / 睡眠 / 补剂，多源归一化（手动、语音文本、摄像头、mmWave）。
- **安全 AI**：Rule Engine 唯一产出剂量 / 阈值 / 医疗判定；LLM 仅经 Model Gateway 调用，输出经 Dose Interceptor 拦截。
- **隐私**：视频 / 图片 / 音频 / 医疗记录不出局域网；云端 LLM 仅收经 Privacy Gateway 脱敏后的文本。
- **告警必达**：红 / 橙告警多通道送达 + Mac / 摄像头扬声器本地兜底，红色未送达目标为 0。
- **可审计**：所有 mutating 操作写不可删除审计日志。

## 2. 架构事实来源（SSOT）

| 文档 | 角色 |
|---|---|
| `docs/ARCHITECTURE_FINAL.md` | **唯一**架构基线 |
| `docs/ENGINEERING_DESIGN.md` | 工程实现蓝图 |
| `docs/TASK_BACKLOG.md` | 任务清单（APC-T001 ~ APC-T059） |
| `docs/PROJECT_STATE.md` | 当前状态 SSOT |
| `docs/HANDOFF.md` | Agent 接手入口 |
| `docs/ADR/` | 架构决策记录 |

冲突优先级：用户指令 > HANDOFF > ARCHITECTURE_FINAL > ENGINEERING_DESIGN > TASK_BACKLOG > 源码历史。

## 3. 技术栈

- **服务端**：Python 3.11+ / FastAPI / Pydantic v2 / SQLAlchemy 2.0 async + asyncpg / Alembic / PostgreSQL 15+ / PowerSync / Mosquitto + aiomqtt / APScheduler / structlog / prometheus_client / OpenTelemetry。
- **安卓**：React Native Android-only + op-sqlite + @powersync/react-native + @react-native-firebase/messaging + @notifee/react-native。
- **固件**：ESP32C6 + PlatformIO + PubSubClient。
- **测试**：pytest + pytest-asyncio + hypothesis + testcontainers + freezegun + ruff + mypy。

## 4. 快速开始

```bash
cd projects/AI-Parenting

# 安装依赖（uv）
make install

# 复制环境变量样例（不要提交真实密钥）
cp .env.example .env

# 启动本地基础设施（PostgreSQL / Mosquitto / PowerSync）
make infra-up
make db-migrate

# 启动开发服务器
make run-dev
# → http://127.0.0.1:8000
# → http://127.0.0.1:8000/docs  (OpenAPI)
# → http://127.0.0.1:8000/healthz
```

## 5. 常用命令

```bash
make lint          # ruff check + format --check
make typecheck     # mypy
make test          # 单元测试（排除 slow/integration）
make test-all      # 全量测试（含 integration，需 DB）
make security-test # 安全回归（Dose/PII/Canary/审计不可删除）
make golden        # 规则黄金用例
make rules-validate # 校验 config/rules/** 规则包

make infra-up      # docker compose up -d
make db-migrate    # alembic upgrade head
make db-seed       # seed_family.py
make docs-check    # 文档一致性检查
make governance-check
```

## 6. 目录结构

```
projects/AI-Parenting/
├── server/              # 服务端（FastAPI + 领域模块）
│   ├── app/             # 业务代码（auth/events/state_engine/rule_engine/...）
│   ├── migrations/      # Alembic
│   ├── scripts/         # seed / run scripts
│   └── tests/           # unit/integration/golden/security/e2e
├── android/             # React Native Android-only
├── firmware/esp32c6/    # mmWave MQTT 固件
├── config/              # rules / devices / routing_plans / notification
├── deploy/              # docker-compose / launchd
├── runtime/             # 本地运行时产物（gitignored，仅留 .gitkeep）
├── tests/               # 跨端 fixtures / e2e / shadow / soak
└── docs/                # 架构 / 工程 / 任务 / 状态 / ADR
```

## 7. 边界（重要）

- 本项目目录与同仓库 `projects/AI-Parenting-Copilot/` **完全隔离**，互不参考、互不修改。
- 本项目状态只在 `projects/AI-Parenting/docs/` 下记录，**不写入工厂根** `docs/DEV_LOG.md` / `CHANGELOG.md` / `PROJECT_STATE.md`。
- 不复制工厂 `_infra/` 实现，只通过适配层引用（Factory-first）。

## 8. 更多

新 Agent 接手请先读 [`docs/HANDOFF.md`](docs/HANDOFF.md)。

<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-08-01 10:45:00
-->

# RUNBOOK_LOCAL_API —— 本地 FastAPI 服务启动与健康检查

## 1. Terminal 1：启动基础设施

路径：

```bash
cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory/projects/AI-Parenting-Copilot
```

venv：保持 `(AI-Project-Incubation-Factory)` 激活。

命令：

```bash
export PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting"
export PARENTING_POWERSYNC__URL="http://127.0.0.1:9081"

make infra-up
make db-migrate
make db-current
```

预期：PostgreSQL healthy，Alembic current 为 `0002_event_notify_trigger (head)`。

## 2. Terminal 2：启动 FastAPI

路径同上，venv 同上。

```bash
cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory/projects/AI-Parenting-Copilot
export PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting"
export PARENTING_POWERSYNC__URL="http://127.0.0.1:9081"

make run-api
```

`make run-api` 是 `make run-dev` 的别名，前台运行 uvicorn：

```text
Uvicorn running on http://127.0.0.1:8000
```

不要在这个终端继续输入 curl；保持它运行。

## 3. Terminal 3：健康检查

路径同上，venv 同上。

推荐先跑 Make target：

```bash
make api-health-smoke
```

也可以手动 curl：

```bash
curl http://127.0.0.1:8000/healthz
curl -X POST "http://127.0.0.1:8000/api/v1/system/health/check?family_id=family-1&baby_id=baby-1"
curl http://127.0.0.1:8000/api/v1/system/health
```

预期：返回 JSON。若某个探针离线，`/api/v1/system/health` 可返回 `degraded`；这不等同于服务未启动。

## 4. 自动启动/关闭型 smoke

如果只想验证服务能启动而不手动开多个终端：

```bash
make api-server-smoke-test
```

该命令会临时在 `127.0.0.1:8766` 启动 uvicorn，检查 `/healthz` 和 system health，然后自动停止。

## 5. 常见错误

### `curl: (7) Failed to connect to 127.0.0.1 port 8000`

含义：FastAPI 进程没有运行。

修复：先在另一个终端执行：

```bash
make run-api
```

### `database mode = dev-mock`

含义：当前启动 FastAPI 的终端没有导出 `PARENTING_DATABASE__URL`。

修复：停止 uvicorn，重新导出 DB URL 后再启动。

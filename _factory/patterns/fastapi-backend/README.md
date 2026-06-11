<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# Pattern：fastapi-backend（可运行的最小 FastAPI 后端脚手架）

> Pattern = 可直接使用的工作代码结构，不是文档描述（KR-004-2）。

## 适用场景
- 需要一个带健康检查、配置管理、日志、单测的 Python Web 后端起点。
- 作为 BUILD 阶段的起步脚手架，复制到 `projects/{name}/` 后改包名即可开干。

## 已知局限
- 仅含最小骨架（健康检查 + 一个示例资源），无数据库/认证（按需自行加）。
- 默认无外部依赖即可跑 `core` 逻辑测试；跑完整 HTTP 需安装 fastapi/uvicorn。

## 最后验证版本
- 2026-06-10：`core` 纯逻辑单测在 Python 3.13 沙箱通过（无需安装 fastapi）。
- HTTP 层需 `uv pip install fastapi uvicorn httpx pytest` 后用 `pytest tests/` 验证。

## 目录
```
fastapi-backend/
├── pyproject.toml
├── src/app/
│   ├── __init__.py
│   ├── config.py        # 配置（禁止硬编码，读 env）
│   ├── core.py          # 纯业务逻辑（无框架依赖，易测）
│   └── main.py          # FastAPI 应用（HTTP 层）
└── tests/
    ├── unit/test_core.py        # 纯逻辑单测（沙箱已验证通过）
    └── integration/test_api.py  # HTTP 集成测试（需装 fastapi/httpx）
```

## 用法
```bash
# 1) 复制脚手架到项目
cp -r _factory/patterns/fastapi-backend projects/my-app
cd projects/my-app

# 2) 安装依赖（国内源）
uv venv && source .venv/bin/activate
uv pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3) 跑纯逻辑单测（无需 fastapi）
python -m pytest tests/unit -q

# 4) 起服务
uvicorn app.main:app --reload --port 8000
# 健康检查：curl http://localhost:8000/health
```

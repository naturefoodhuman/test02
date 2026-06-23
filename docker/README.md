<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-23 11:58:00
-->

# FORGE Network Docker Services

This directory contains local-only Docker Compose services for the network
feature increment.

## Services

- `searxng` → `127.0.0.1:8080`
- `crawl4ai` → `127.0.0.1:11235`

## Start

```bash
cd docker
export SEARXNG_SECRET_KEY="replace-with-local-random-secret"
docker compose up -d
```

## Verify

```bash
curl 'http://127.0.0.1:8080/search?q=test&format=json'
curl 'http://127.0.0.1:11235/health'
```

All ports are bound to `127.0.0.1` only, per the Local First architecture.

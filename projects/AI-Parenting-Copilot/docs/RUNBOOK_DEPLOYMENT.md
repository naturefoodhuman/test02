<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-07-09 10:10:00
-->


# Deployment Runbook — AI Parenting Copilot

## Dev bootstrap order

```bash
cp deploy/.env.example deploy/.env
make infra-up
make db-migrate
python3 server/scripts/seed_family.py
make run-dev
```

## launchd

Example plists live in `deploy/launchd/`:

- `com.parenting.server.plist`
- `com.parenting.fregata.plist`
- `com.parenting.backup.plist`

Logs should be written under `runtime/logs/`, which is gitignored.

## Notes

- Do not commit `.env`, camera credentials, FCM JSON, WiFi passwords, or `runtime/secrets`.
- Fregata is a placeholder until the local binary/model path is configured on the Mac.
- The current worker model is FastAPI lifespan/in-process workers, per engineering design.

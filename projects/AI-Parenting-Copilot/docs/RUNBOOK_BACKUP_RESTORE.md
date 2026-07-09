<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-07-09 09:20:00
-->


# Backup / Restore Runbook — AI Parenting Copilot

## Scope

This runbook covers local PostgreSQL dumps and encrypted media archives for the
household Mac deployment. It deliberately does not back up plaintext `.env`, camera
credentials, FCM service account JSON, or model API keys.

## Backup

```bash
cd projects/AI-Parenting-Copilot
make db-current
# Dry-run plans only:
python3 -m pytest tests/test_backup_tasks.py -q
```

Production backup execution should use `pg_dump --format=custom` with the local
PostgreSQL URL from `.env`, then archive `runtime/media/files/*.bin` and thumbnails.

## Restore Drill

1. Provision empty PostgreSQL database.
2. Run `alembic upgrade head`.
3. Restore custom dump with `pg_restore --clean --if-exists` after stopping the app.
4. Restore encrypted media archive to `runtime/media/`.
5. Run `make test` and verify `/healthz`.

## Security Notes

- Do not back up `.env` or `runtime/secrets` into shared storage.
- Media files are already encrypted by `MediaStorageService`; keep them encrypted in NAS.
- Verify restore at least once before production cutover.

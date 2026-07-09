<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-07-09 14:30:00
-->

# P0 Release Checklist — AI Parenting Copilot

## Infrastructure

- [ ] Docker Desktop running on Mac.
- [ ] `make infra-up` shows PostgreSQL, Mosquitto and PowerSync healthy.
- [ ] `make db-migrate` reaches Alembic head.
- [ ] `python3 -m alembic -c alembic.ini current` prints `0002_event_notify_trigger` or later.

## Safety and Privacy

- [ ] `make security-test` passes.
- [ ] Dose Interceptor blocks LLM free-text doses.
- [ ] Privacy Adapter redacts PII before cloud fallback.
- [ ] Canary leak is blocked.
- [ ] audit_log update/delete is rejected by DB trigger.

## Alerting

- [ ] FCM payload includes only `alert_id`, `level`, `type`.
- [ ] Mac speaker test audible in living room.
- [ ] Android high-priority/full-screen permission granted.
- [ ] Camera speaker fallback configured if available.
- [ ] Red alert escalation 0s / 60s / 90s verified.
- [ ] Ack cancels all channels.

## Camera / mmWave Shadow

- [ ] Camera vendor cloud disabled and verified.
- [ ] Sleep session ROI manually configured.
- [ ] `tests/shadow/camera_mmwave_shadow_harness.py` runs on mock data.
- [ ] Seven-night shadow report reviewed for false positives.
- [ ] mmWave single-signal red alert remains impossible.

## Android MVP

- [ ] Android build / install succeeds.
- [ ] Battery optimization / auto-start guide completed.
- [ ] Offline Quick Record creates pending feeding event.
- [ ] Network restore syncs event to Mac.
- [ ] Today shows derived feeding state.

## Backup / Restore

- [ ] `make backup-dry-run` output reviewed.
- [ ] Real `pg_dump --format=custom` backup generated.
- [ ] Encrypted media archive generated.
- [ ] Restore drill completed on empty database.

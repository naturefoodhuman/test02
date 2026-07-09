<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-07-09 14:30:00
-->

# MVP Feeding Roundtrip Semi-Automated Checklist

1. Put Android device offline.
2. Create Quick Record feeding payload: `90ml`.
3. Verify local event has `pending_sync=true`.
4. Restore network.
5. Verify PowerSync uploads event to PostgreSQL `observation_event`.
6. Verify normalization creates `feeding_log`.
7. Verify state engine updates `derived_baby_state.snapshot.feeding_24h_ml`.
8. Verify Today displays the updated feeding state.

Current automated dev substitute: `tests/test_event_to_state_pipeline.py`.

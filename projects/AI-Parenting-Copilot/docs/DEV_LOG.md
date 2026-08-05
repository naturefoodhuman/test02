<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-08-05 02:05:00
-->


# DEV LOG —— AI Parenting Copilot 逐轮开发日志

## Latest Development Index

- **当前状态 SSOT**：`docs/PROJECT_STATE.md`
- **任务状态 SSOT**：`docs/TASK_BACKLOG.md`
- **最新完成**：用户本机 `api-db-smoke-test` 复验通过后，`APC-T037/T042/T043` 已 DONE；新增 Rule Review Packet 生成器，继续压缩 `APC-T022/T023` 人审成本。
- **最新修复**：`make test` 即使 shell 保留 `PARENTING_DATABASE__URL` 也强制 dev-mock；非 integration pytest 自动隔离 DB env；新增 `make api-db-smoke-test`；EvidencePolicy DB activate 对同一版本幂等，避免重复运行 integration 时唯一键冲突。
- **最新继续开发**：新增 Android Quick Record Copilot text parse → local pending save flow；新增 RN/TS `copilotFlow.ts` 串联 `/api/v1/copilot/query`、record candidate confirm 与 local fallback；native pending drain 增加 `/api/v1/sync/heartbeat` best-effort 上报与逐条异常隔离；PendingEventsActivity 使用 ApiSettings/SecureSession 并保存 last drain；AlertAckDrainer 异常时重新入队 ack；扩展 DB API smoke 覆盖 Copilot query/confirm、FamilyMemory confirm audit 与 P0 Rule Evaluation；修复 DB smoke Memory event_type_counts 断言，使其匹配 feeding + diaper + mmwave_telemetry 的实际短上下文；Scheduler API trigger 新增 create_alert reminder bridge，可把 vaccine/supplement 等蓝色提醒写入 AlertStore；Camera ISAPI/Fregata adapters 从 placeholder 推进到注入式 HTTP bridge；Rule Review Packet 可输出 rule pack hash、golden case pass/fail 与人审 blocker；新增 launchd plist static validator，拦截 /tmp 日志路径等部署错误；新增 backup manifest verifier，校验 dump/media archive manifest 并输出 restore next commands；新增 red alert fake-channel escalation report，验证 0/60/90s escalation、trigger-only FCM payload 与 ack cancel；修复 ESP32C6 firmware mock JSON 字符串并新增 firmware static preflight；新增 mmWave fixture replay report 与 Android/PowerSync E2E contract report；基于 assembleDebug、static tests、contract report 与 server tests 解除 T046/T048/T049/T050/T051/T053/T055。
- **当前测试基线**：用户 Mac `make db-integration-test` → `5 passed, 1 warning`；沙盒 `make test` → `180 passed, 8 deselected, 1 warning`；`make lint/typecheck/security/e2e/shadow/rules/docs-check` 通过；无 DB URL 时 DB integration/smoke 按预期 skipped。
- **当前依赖规则**：uv-first；`ensure-dev-deps` 优先 `uv pip install --python <venv-python> -e .[dev]`，`install-dev` 已改为 uv pip，不直接调用 pip。

---

## 第 99 轮 · 2026-08-05（APC Backlog patch plan）

**目标**：继续推进剩余 BLOCKED 的安全关闭流程，在 closeout recommendations 之后生成 dry-run TASK_BACKLOG patch plan，做到“可一键看差异，但不自动改状态”。

**完成内容**：

- 新增 `server/app/ops/backlog_patch_plan.py`：读取 closeout recommendations，定位 `TASK_BACKLOG.md` 中对应任务状态行，生成 old/new diff 风格 patch plan。
- 新增 `server/scripts/apc_backlog_patch_plan.py` 与 `make apc-backlog-patch-plan`。
- 新增 `tests/test_backlog_patch_plan.py`，覆盖 ready task 的 DONE 状态行建议、blocked task 保留、JSON/Markdown 写出。
- 该工具不修改 `TASK_BACKLOG.md`；只有外部证据通过 closeout gate 后，才生成可审核状态变更建议。

**验证**：

```bash
python3 -m pytest tests/test_backlog_patch_plan.py tests/test_closeout_recommendation.py -q
# 4 passed
make apc-backlog-patch-plan
make lint
make typecheck
make test
# 218 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；patch plan 只生成 dry-run 建议，不自动关闭 APC 任务。

---

## 第 98 轮 · 2026-08-05（External validation bundle）

**目标**：继续压缩用户本机/设备验收步骤，把 external validation plan、evidence templates、rule signoff templates、closeout recommendations 打包为一个可交付目录。

**完成内容**：

- 新增 `server/app/ops/external_validation_bundle.py`：一键生成 external validation plan、所有 evidence templates、vaccine/growth signoff templates、closeout recommendations 和 bundle manifest。
- 新增 `server/scripts/external_validation_bundle.py` 与 `make external-validation-bundle`。
- 新增 `tests/test_external_validation_bundle.py`，验证 bundle 写出所有模板和 manifest。
- Bundle 仍不替代真实外部验收；只是把验收输入材料集中到 `runtime/reports/external-validation-bundle/`。

**验证**：

```bash
python3 -m pytest tests/test_external_validation_bundle.py tests/test_external_validation_plan.py tests/test_closeout_recommendation.py -q
# 6 passed
make external-validation-bundle
make lint
make typecheck
make test
# 216 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；bundle 是文件打包工具，不自动关闭任务或批准外部证据。

---

## 第 97 轮 · 2026-08-05（APC closeout recommendations）

**目标**：继续推进剩余 BLOCKED 的自动化关闭流程，在 closeout gate 之后生成可审核的 Backlog 状态建议，避免后续手工改状态时漏改/误改。

**完成内容**：

- 新增 `server/app/ops/closeout_recommendation.py`：把 closeout gate 的 `ready_to_close/blocked` 结果渲染为建议状态、建议 `TASK_BACKLOG.md` 状态行、依赖与剩余原因。
- 新增 `server/scripts/apc_closeout_recommendations.py` 与 `make apc-closeout-recommendations`。
- 新增 `tests/test_closeout_recommendation.py`，覆盖 DONE/BLOCKED 状态行渲染和 JSON/Markdown 写出。
- 该 report 只给建议，不直接修改 `TASK_BACKLOG.md`，防止外部证据未经审查被自动关闭。

**验证**：

```bash
python3 -m pytest tests/test_closeout_recommendation.py tests/test_apc_closeout_gate.py -q
# 5 passed
make apc-closeout-recommendations
make lint
make typecheck
make test
# 214 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；recommendation report 只读 closeout gate，不改状态、不批准生产规则、不替代外部验收。

---

## 第 96 轮 · 2026-08-04（APC closeout gate）

**目标**：继续推进剩余 BLOCKED 的自动化关闭流程，把 rule signoff 与 external evidence 汇总为一个 closeout gate，后续用户本机/设备证据填好后可一键判断哪些 APC 可关闭。

**完成内容**：

- 新增 `server/app/ops/apc_closeout.py`：读取 rule signoff JSON 与 external evidence JSON，对剩余 `APC-T022/T023/T030/T036/T038/T039/T040/T041/T044/T059` 逐项判断 `ready_to_close` 或 `blocked`。
- 新增 `server/scripts/apc_closeout_gate.py` 与 `make apc-closeout-gate`，输出 `runtime/reports/apc-closeout-gate.json`。
- 新增 `tests/test_apc_closeout_gate.py`，覆盖无证据全部阻塞、T044 完整 evidence 可关闭、dev_shadow signoff 不能关闭 production vaccine。
- 扩展 external validation plan，补齐 `APC-T030` 与 `APC-T036` 依赖型外部验收项。

**验证**：

```bash
python3 -m pytest tests/test_apc_closeout_gate.py tests/test_external_evidence.py -q
# 7 passed
make apc-closeout-gate
make lint
make typecheck
make test
# 212 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；closeout gate 只生成关闭建议，不直接修改 backlog 或自动批准生产规则/设备验收。

---

## 第 95 轮 · 2026-08-04（External evidence verifier）

**目标**：继续推进剩余 10 个外部 blocker 的闭环，把“用户说复验通过”变成可机器校验的 evidence JSON，减少后续人工同步错误。

**完成内容**：

- 新增 `server/app/ops/external_evidence.py`：为 external validation plan 中每个 task 生成 evidence template，并校验 status/operator/completed_at/required evidence keys。
- 新增 `server/scripts/external_evidence.py` 与 `make external-evidence-template`。
- 新增 `tests/test_external_evidence.py`，覆盖 T044/T059 template、完整 evidence 接受、缺失字段拒绝、template 写入。
- 该工具不替代真实人审/设备/NAS/soak，只把外部验收结果标准化成可审计输入。

**验证**：

```bash
python3 -m pytest tests/test_external_evidence.py tests/test_external_validation_plan.py -q
# 6 passed
make external-evidence-template
make lint
make typecheck
make test
# 209 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；只新增外部验收证据模板和静态校验。

---

## 第 94 轮 · 2026-08-04（Rule signoff validator）

**目标**：继续推进 `APC-T022/T023` 的外部人审闭环，把 reviewer sign-off 从自由文本变成可机器校验的 JSON artifact。

**完成内容**：

- 新增 `server/app/rule_engine/review_signoff.py`：校验 signoff artifact 的 domain、region、version、rule pack hash、reviewer、reviewed_at、scope 和 checklist。
- 新增 `server/scripts/validate_rule_signoff.py` 与 `make rule-signoff-template`。
- 支持 `dev_shadow` 与 `production` scope；当前 dev/fixture rule pack 不能被 production signoff 误批准。
- 新增 `tests/test_rule_review_signoff.py`，覆盖 template hash、dev_shadow signoff、production fixture rejection、hash mismatch。

**验证**：

```bash
python3 -m pytest tests/test_rule_review_signoff.py -q
# 4 passed
make rule-signoff-template
make lint
make typecheck
make test
# 205 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；signoff validator 不自动激活规则，只防止人审 artifact 与当前 rule pack 不一致或误把 dev fixture 当生产批准。

---

## 第 93 轮 · 2026-08-04（External validation plan）

**目标**：继续压缩剩余 BLOCKED 的执行不确定性，把所有必须依赖人审/硬件/NAS/长稳态的任务整理成一份可执行外部验收计划。

**完成内容**：

- 新增 `server/app/ops/external_validation.py`：列出剩余外部 blocker 的 task_id、resource_type、blocked_by、commands、evidence_required、success_criteria。
- 新增 `server/scripts/external_validation_plan.py` 与 `make external-validation-plan`，输出 JSON + Markdown 到 `runtime/reports/`。
- 覆盖剩余外部任务：`APC-T022/T023/T038/T039/T040/T041/T044/T059`，并显式说明自动化检查不能替代人审/真实设备/真实 NAS/7-night soak。
- 新增 `tests/test_external_validation_plan.py`，确保计划覆盖剩余关键 blocker 且每项都有命令、证据和成功标准。

**验证**：

```bash
python3 -m pytest tests/test_external_validation_plan.py -q
# 2 passed
make external-validation-plan
make lint
make typecheck
make test
# 201 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；该计划只组织外部验收，不替代真实人审、设备、NAS 或长期 soak。

---

## 第 92 轮 · 2026-08-04（P0 readiness aggregate report）

**目标**：继续推进 `APC-T059`，把所有无外部资源即可完成的发布前检查汇总成一个 P0 readiness 聚合报告，明确剩余只有人审/硬件/长稳态。

**完成内容**：

- 新增 `server/app/ops/p0_readiness.py`：聚合 Rule Review Packet、Android E2E contract、Android Notification contract、Deployment Readiness、Backup Manifest verifier、mmWave replay、Firmware preflight、Red Alert simulation、Shadow harness、Release checklist 关键项。
- 新增 `server/scripts/p0_readiness_report.py` 与 `make p0-readiness`。
- 新增 `tests/test_p0_readiness_report.py`，断言所有自动化检查为 `ok`，报告状态为 `ready_for_external_validation`，并列出仍需外部验收的 blockers。
- P0 readiness report 明确列出 remaining external blockers：Vaccine/Growth 人审、Camera/VLM 设备、真实 MQTT/mmWave soak、PlatformIO flash、NAS/restore drill、7-night shadow/soak。

**验证**：

```bash
python3 -m pytest tests/test_p0_readiness_report.py tests/test_shadow_soak_release.py -q
# 3 passed
make p0-readiness
# automated_status=ready_for_external_validation
make lint
make typecheck
make test
# 199 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；聚合报告只汇总现有自动化检查和外部 blocker，不替代真实人审/硬件/7-night soak。

---

## 第 91 轮 · 2026-08-04（APC-T047/T052/T054/T056/T057 accepted）

**目标**：按用户要求一次性至少完成 5 个 APC 任务，继续把已实现并具备自动化合同报告/回归测试的任务从 BLOCKED 转 DONE。

**状态变更**：

- `APC-T047` Android Sync / pending_sync：BLOCKED → DONE。
- `APC-T052` Android Notification / FullScreenIntent / fallback：BLOCKED → DONE。
- `APC-T054` DevOps run scripts / launchd / deployment samples：BLOCKED → DONE。
- `APC-T056` MVP E2E feeding roundtrip：BLOCKED → DONE。
- `APC-T057` Red alert E2E：BLOCKED → DONE。

**完成依据**：

- `APC-T047`：Android local schema、native SQLite pending store、TS/native drain、heartbeat、JobScheduler、Android/PowerSync contract report 全部通过。
- `APC-T052`：新增 Android notification contract report，覆盖 manifest permissions、full-screen Activity、trigger-only payload、high importance channel、local fallback、ack retry、TS FCM detail fetch。
- `APC-T054`：deployment readiness report、launchd validator、run scripts、local API runbook、health/server smoke targets 全部覆盖。
- `APC-T056`：dev API feeding roundtrip、Android E2E contract report、native offline pieces、server sync contract sample 全部覆盖。
- `APC-T057`：red alert API E2E、fake-channel escalation report、trigger-only payload、ack cancel、feedback regression 全部覆盖。

**验证**：

```bash
python3 -m pytest tests/test_android_notification_contract.py tests/test_deployment_readiness.py tests/e2e/test_android_e2e_contract_report.py -q
# 3 passed
make android-notification-contract
make deployment-readiness
make android-e2e-contract
make e2e-fake-test
make lint
make typecheck
make test
# 198 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；真实硬件/FCM/长期 soak 不在这些代码任务中伪造，继续由设备/发布硬化任务跟踪。

---

## 第 90 轮 · 2026-08-04（APC-T050/T051/T053 accepted）

**目标**：按用户“至少完成 3 个 APC 任务”的要求，继续把已满足代码/验证条件的 Android core screens 从 BLOCKED 转 DONE，真实设备端到端仍集中留给 E2E 任务。

**状态变更**：

- `APC-T050` Android Timeline：BLOCKED → DONE。
- `APC-T051` Android Alert Center：BLOCKED → DONE。
- `APC-T053` Android Sleep Session UI：BLOCKED → DONE。

**完成依据**：

- 用户本机 `./gradlew assembleDebug` 已通过。
- Timeline：TS fetch/correction/delete/duplicate hint，native TimelineActivity server refresh route 已由 Android E2E contract report 覆盖。
- Alert Center：TS list/deliveries/dispatch/ack/feedback，native alert list/feedback/ack drain 与 exception-safe ack retry 已由 contract/static tests 覆盖。
- Sleep Session：TS start/pause/resume/end/ROI/camera-events/shadow-summary/shadow-evaluate，native start/ROI/camera-events/action routes 已由 contract/static tests 覆盖。
- 真机 Android/PowerSync full E2E 仍由 `APC-T056` 跟踪；真实 FCM/Notifee 仍由 `APC-T057` 跟踪。

**验证**：

```bash
python3 -m pytest tests/e2e/test_android_e2e_contract_report.py tests/test_android_features.py tests/test_android_native_skeleton.py -q
# 13 passed
make android-e2e-contract
make lint
make typecheck
make test
# 196 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；本轮仅接受已完成 Android screen code tasks，真实设备 E2E 仍单独跟踪。

---

## 第 89 轮 · 2026-08-04（APC-T046/T048/T049/T055 accepted）

**目标**：按用户要求加速完成 APC 任务，基于已通过的 Android `assembleDebug`、API DB smoke、自动化 static/API/contract tests，解除多个仅代码/fixture 层面的阻塞。

**状态变更**：

- `APC-T046` Android Auth：BLOCKED → DONE。
- `APC-T048` Android Quick Record：BLOCKED → DONE。
- `APC-T049` Android Today：首页：BLOCKED → DONE。
- `APC-T055` Dev Fixtures / Fake Services / Mock Publishers：BLOCKED → DONE。

**完成依据**：

- 用户本机 `./gradlew assembleDebug` 已通过。
- Android Auth：TS `authService`、native `LoginActivity`、Keystore `SecureSessionStore`、device registration route 与 launcher entry 均由 Android E2E contract report 覆盖。
- Quick Record：native offline `insertPending`、Copilot text parse、本地 deterministic fallback、pending drain route 与 heartbeat route 均由 tests/contract report 覆盖。
- Today：首页 pending sync visibility、server health route、TS state/health/alerts helper 均由 tests/contract report 覆盖。
- Dev Fixtures：Fake notification channels、mock mmWave publisher、radar fixtures、mmWave replay report、red alert fake-channel report、security fake tests 均已可自动运行。
- 真实 Android/PowerSync full E2E 仍保留在 `APC-T056`；真实 FCM/Notifee 仍保留在 `APC-T057`。

**验证**：

```bash
python3 -m pytest tests/e2e/test_android_e2e_contract_report.py tests/test_android_features.py tests/test_android_native_skeleton.py -q
# 13 passed
make android-e2e-contract
make lint
make typecheck
make test
# 196 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；本轮只是把已完成并验证的 Android/fixtures 代码任务转为 DONE，真实设备 E2E 仍单独跟踪。

---

## 第 88 轮 · 2026-08-04（mmWave replay + Android E2E contract reports）

**目标**：继续推进 `APC-T040/T055/T056`，把无硬件/无真机环境下的 mmWave 和 Android/PowerSync E2E 合同验证继续自动化。

**完成内容**：

- 新增 `server/app/mmwave/replay.py`：读取 `tests/fixtures/radar_frames.jsonl`，通过 parser/mapper 生成 replay report，统计 total frames、presence、abnormal、signal types 和 optional ObservationEvent mapping。
- 新增 `server/scripts/replay_mmwave_fixture.py` 与 `make mmwave-replay`。
- 新增 `server/app/sync/e2e_contract.py`：静态验证 Android sync schema、pending drain、heartbeat route、QuickRecord offline fallback、Today pending visibility，并用 server sync contract validator 校验 sample event。
- 新增 `server/scripts/android_e2e_contract_report.py` 与 `make android-e2e-contract`。
- 新增 regression tests：`tests/test_mmwave_replay.py`、`tests/e2e/test_android_e2e_contract_report.py`。

**验证**：

```bash
python3 -m pytest tests/test_mmwave_replay.py tests/e2e/test_android_e2e_contract_report.py tests/test_sync_contract.py -q
# 5 passed
make mmwave-replay
make android-e2e-contract
make lint
make typecheck
make test
# 196 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；reports 只验证现有 parser/mapper/sync contracts，不替代真实 MQTT broker、PowerSync 或 Android device E2E。

---

## 第 87 轮 · 2026-08-04（ESP32C6 firmware static preflight）

**目标**：继续推进 `APC-T041`，先修复 firmware skeleton 中会阻断编译的 mock JSON 字符串，并增加无硬件/无 PlatformIO 的静态 preflight。

**完成内容**：

- 修复 `firmware/esp32c6/src/main.cpp` 的 JSON 字符串转义，`buildMockPayload()` 现在可生成合法 JSON 形态。
- 增加 `Serial.println(payload)`，便于本机/串口调试发布内容。
- 新增 `firmware/esp32c6/tools/preflight.py`，校验 PlatformIO board、PubSubClient dependency、config placeholder、MQTT topic、payload fields、mock JSON shape。
- 新增 `make firmware-preflight`。
- 新增 `tests/test_firmware_preflight.py`，覆盖 preflight 与 payload shape。

**验证**：

```bash
python3 -m pytest tests/test_firmware_skeleton.py tests/test_firmware_preflight.py -q
# 3 passed
make firmware-preflight
make lint
make typecheck
make test
# 193 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；仍是 firmware skeleton/preflight，不宣称 PlatformIO 编译或真实硬件通过。

---

## 第 86 轮 · 2026-08-04（Red alert escalation report）

**目标**：继续推进 `APC-T057`，把红色告警 E2E substitute 从基本 dispatch/ack 扩展到 0/60/90 秒升级链路报告。

**完成内容**：

- 新增 `server/app/notification/escalation_report.py`：使用真实 `EscalationStateMachine` + `NotificationOrchestrator` + fake channels 生成确定性红警升级报告。
- 新增 `server/scripts/simulate_red_alert_escalation.py` 与 `make red-alert-sim`，输出 JSON 报告到 `runtime/reports/`。
- 新增 `tests/e2e/test_red_alert_escalation_report.py`，验证 initial fanout、Mac repeat、phone/camera escalation、ack cancel、trigger-only payload。
- `make e2e-fake-test` 覆盖红警升级报告，仍不调用真实 FCM/音频/摄像头。

**验证**：

```bash
python3 -m pytest tests/e2e/test_red_alert_escalation_report.py tests/test_escalation.py -q
# 3 passed
make red-alert-sim
make e2e-fake-test
# 4 passed, 1 warning
make lint
make typecheck
make test
# 191 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；simulation 使用 Notification Orchestrator/fake channels，不直接投递真实告警，不绕过 trigger-only payload 约束。

---

## 第 85 轮 · 2026-08-04（Backup manifest verifier）

**目标**：继续推进 `APC-T044`，把备份/恢复从 dry-run plan 推进到 manifest verification，减少真实 NAS/restore drill 前的错误面。

**完成内容**：

- 新增 `server/app/backup/verification.py`：校验 backup manifest JSON、`.dump` 扩展名、`.tar.gz` 媒体归档扩展名、可选文件存在性、媒体归档安全路径和 scope。
- 新增 `server/scripts/verify_backup_manifest.py` 与 `make backup-verify-dry-run`。
- `backup-verify-dry-run` 会生成 restore drill manifest，并输出后续真实本地命令：`pg_restore --list`、`pg_restore --clean`、`tar -tzf`。
- 新增 `tests/test_backup_verification.py`，覆盖 dry-run manifest、安全 media archive 与 unsafe tar path 拒绝。

**验证**：

```bash
python3 -m pytest tests/test_backup_verification.py tests/test_backup_tasks.py -q
# 6 passed
make backup-verify-dry-run
make lint
make typecheck
make test
# 190 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；仅增加备份恢复演练静态/本地文件校验，不接触真实 NAS 或覆盖生产库。

---

## 第 84 轮 · 2026-08-03（launchd static validator）

**目标**：继续推进 `APC-T054/T044`，把 launchd 配置从“存在文件”提升为可自动校验，降低 Mac 本地长期运行排错成本。

**完成内容**：

- 新增 `server/app/ops/launchd_validator.py`，使用 stdlib `plistlib` 校验 launchd plist XML、Label、ProgramArguments、log paths 与 RunAtLoad/WorkingDirectory 约束。
- 新增 `make launchd-validate`。
- 修正 `deploy/launchd/com.parenting.backup.plist` 日志路径：`/tmp` → `runtime/logs/`。
- 新增 `tests/test_launchd_validator.py`，覆盖全部 launchd plist 和 `/tmp` 日志拒绝规则。

**验证**：

```bash
python3 -m pytest tests/test_launchd_validator.py tests/test_backup_tasks.py -q
# 5 passed
make launchd-validate
make lint
make typecheck
make test
# 187 passed, 8 deselected, 1 warning
make docs-check
```

**架构影响**：

- 无架构变更；仅增加部署配置静态校验，不引入新运行时基础设施。

---

## 第 83 轮 · 2026-08-03（Rule Review Packet generator）

**目标**：继续推进 `APC-T022/T023`，把 Vaccine/Growth 生产规则审查从“读源码”压缩为可交付的人审包，降低人工验收成本。

**完成内容**：

- 新增 `server/app/rule_engine/review_packet.py`：汇总 rule pack metadata、SHA256 hash、rule ids、source、人审 blocker 与 golden-case 运行结果。
- 新增 `server/scripts/generate_rule_review_packet.py` 与 `make rule-review-packet`：输出 JSON + Markdown 到 `runtime/reports/`。
- 覆盖所有 P0 rule domains：medication、triage、thresholds、vaccine、growth。
- Vaccine/Growth 明确保留 `pending_human_review`，不伪造生产审查；packet 明确提示官方 CN 免疫规划审查、完整 WHO LMS 表导入/审查仍是 blocker。
- 新增 `tests/test_rule_review_packet.py`，断言 golden cases 全通过、hash 存在、人审 blocker 存在、Markdown/JSON 可生成。

**验证**：

```bash
python3 -m pytest tests/test_rule_review_packet.py tests/test_vaccine_rules.py tests/test_growth_rules.py tests/test_medication_rules.py tests/test_triage_threshold_rules.py -q
# 10 passed
make rule-review-packet
# review_status=pending_human_review
```

**架构影响**：

- 无架构变更；Rule Review Packet 只做审查证据打包，不改变 Rule Engine 决策逻辑，不把 dev fixture 标记为 production approved。

---

## 第 82 轮 · 2026-08-03（Camera ISAPI/Fregata HTTP bridge）

**目标**：继续推进 `APC-T038/T039`，把摄像头相关 placeholder adapter 提升为可注入、可测试的真实 HTTP bridge，同时不要求本轮具备真实设备。

**完成内容**：

- `ISAPIClient.health()` 支持真实 `/ISAPI/System/status` HTTP health probe，支持注入 fake async HTTP client 做无设备测试。
- `FregataBridge.analyze_snapshot()` 支持向 Fregata endpoint POST snapshot bytes，并把 `events` / `detections` 规范化为 shadow events。
- Fregata/ISAPI 异常均返回 shadow/offline 结果，不直接生成红橙告警，不绕过 Camera shadow pipeline。
- 新增 camera adapter unit tests 覆盖 ISAPI health URL 与 Fregata shadow events normalization。

**验证**：

```bash
python3 -m pytest tests/test_camera_adapters.py -q
# 7 passed, 1 warning
make lint
make typecheck
make test
# 183 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；Camera/Fregata 仍保持 shadow-mode，真实设备/RTSP/ISAPI/Fregata endpoint 验收仍需本地硬件环境。

---

## 第 81 轮 · 2026-08-03（Scheduler reminder alert bridge + task unblocking）

**目标**：利用用户本机复验结果解除已满足 DoD 的 Sleep/Media/Export 阻塞，并继续推进 Scheduler 提醒闭环。

**完成内容**：

- 根据用户本机 `api-db-smoke-test` 复验通过，`APC-T037`、`APC-T042`、`APC-T043` 更新为 DONE。
- `POST /api/v1/scheduler/jobs/{job}/trigger` 新增可选 query：`family_id`、`baby_id`、`create_alert`。
- `POST /api/v1/scheduler/trigger-all` 同步支持 `create_alert`。
- 当 job result 包含 `alert_level` 且 `create_alert=true` 时，通过 AlertStore 创建 `scheduler.{job}` reminder alert，并审计 `alert.create` / `scheduler.trigger`。
- 新增 regression test：vaccine_due scheduler trigger 可生成 blue reminder alert；API DB smoke 也覆盖 scheduler reminder alert 与 `scheduler.trigger` audit。

**验证**：

```bash
python3 -m pytest tests/test_scheduler_api.py tests/test_scheduler_jobs.py tests/test_scheduler_worker.py -q
# 8 passed, 1 warning
make lint
make typecheck
make test
# 181 passed, 8 deselected, 1 warning
make api-db-smoke-test
# sandbox: 1 skipped（无本地 DB URL）；用户本机已复验通过基础 DB smoke
make security-test
make e2e-fake-test
make shadow-test
make rules-validate
make restore-dry-run
make docs-check
cd ../.. && make docs-check
# Blockers: 0
```

**架构影响**：

- 无架构变更；Scheduler 只创建提醒型 Alert 记录，不直接投递；后续投递仍必须经 Notification Orchestrator。

---

## 第 80 轮 · 2026-08-03（Workspace cleanup + API DB smoke assertion fix）

**目标**：先清理沙盒工作区垃圾文件并修复用户本机 `api-db-smoke-test` 失败。

**完成内容**：

- 定位失败原因：DB smoke 在 Memory snapshot 前已创建 feeding、Copilot-confirmed diaper、mmWave telemetry 三类 ObservationEvent；`SQLAlchemyMemoryStore._short_context()` 按最近 72h 所有未删除事件统计 `event_type_counts`，因此旧断言只期待 `{feeding: 1}` 与实际业务逻辑不符。
- 修复断言：改为分别验证 `feeding == 1`、`diaper == 1`、`mmwave_telemetry == 1`。
- 同步用户本地复验结果：`./gradlew assembleDebug` 已成功；Android 相关任务仍等待真机/device/PowerSync/FCM 等实体验收。
- 工作区清理：已清除沙盒 `.local` 开发依赖缓存/包与 Python/pytest/mypy/ruff cache，并执行 git gc；`/home/user` 从约 198M 降到约 22M，低于 Arena workspace snapshot budget。

**验证**：

```bash
python3 -m pytest tests/test_android_native_skeleton.py tests/test_android_features.py tests/test_orchestrator.py tests/test_rules_admin_api.py -q
# 18 passed, 1 warning
make lint
# All checks passed.
make typecheck
# Success: no issues found in 188 source files
make test
# 180 passed, 8 deselected, 1 warning
make api-db-smoke-test
# sandbox: 1 skipped（无本地 DB URL）；用户 Mac DB 环境需复验
make docs-check
cd ../.. && make docs-check
# Blockers: 0
```

**架构影响**：

- 无架构变更；Memory short_context 继续反映真实最近事件，Rule/Copilot/Android offline-first 边界不变。

---


## 第 78 轮 · 2026-08-02（Native pending drain heartbeat hardening）

**目标**：继续加固 Android native offline-first 同步链路，保证 drain 失败不会丢本地记录，并让 native fallback 与服务端 sync_state 保持一致。

**完成内容**：

- `PendingSyncDrainer` 对每条 pending event 的上传增加 exception 隔离；单条网络失败不会中断后续 drain，也不会 markSynced。
- drain 完成后 best-effort 上报 `/api/v1/sync/heartbeat`，使用 SecureSession 中的 device/family 与当前 pending count。
- heartbeat 失败不影响本地事件保存/同步状态，继续遵守 Android offline record must not be lost。
- Static tests 覆盖 native drainer heartbeat contract。

**验证**：

```bash
python3 -m pytest tests/test_android_native_skeleton.py tests/test_android_features.py -q
# 12 passed
make lint
make typecheck
make test
# 180 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更；sync heartbeat 走既有 Sync API，失败不影响本地 pending 可靠性。

---

## 第 77 轮 · 2026-08-02（Quick Record Copilot flow + DB smoke expansion）

**目标**：继续推进 Android Quick Record 与 P0 Copilot/API 闭环，减少用户手动验证前的服务端/客户端契约缺口。

**完成内容**：

1. Android native Quick Record：
   - 新增自由文本输入与“Parse text with Copilot and save locally”按钮。
   - 调用 `/api/v1/copilot/query` 获取 Logger Copilot record candidate。
   - 解析成功后写入 native `LocalEventStore.insertPending()`；网络/API 不可用时用本地 deterministic fallback 保存 pending，继续保证离线记录不丢失。
2. Android RN/TS Quick Record：
   - 新增 `android/src/features/quick_record/copilotFlow.ts`。
   - 支持 `fetchCopilotRecordCandidate()`、`confirmCopilotRecordCandidate()`、`createLocalEventFromCopilotText()`。
   - 服务器不可用时回退到本地 deterministic parser。
3. DB API smoke：
   - 扩展 Copilot query → candidate → confirm → audit 覆盖。
   - 扩展 FamilyMemory confirm 后的 FamilyKnowledge list 与 audit 覆盖。
   - 扩展 medication/triage/vaccine/growth Rule Evaluation API smoke，确保 App/Copilot 医疗/剂量路径只走 Rule Engine。

**验证**：

```bash
python3 -m pytest tests/test_android_features.py tests/test_android_native_skeleton.py tests/test_orchestrator.py tests/test_rules_admin_api.py -q
make lint
make typecheck
make test
# 当前沙盒无 DB/Mac Android SDK；api-db-smoke-test 与 assembleDebug 仍需用户本机环境复验。
```

**架构影响**：

- 无架构变更。Copilot 仅产出候选，确认/持久化走现有 API 与 audit；剂量/分诊/疫苗/生长仍只经 Rule Engine；Android 保存仍先落本地 pending。

---

## 第 76 轮 · 2026-08-02（Composite camera shadow evaluate API）

**目标**：把 fusion 与 VLM shadow 两个步骤组合成单一 API，便于 App/Shadow harness 一次性完成 shadow decision、clip plan、camera_event 与 optional VLM dry-run/dispatch。

**完成内容**：

- 新增 `POST /api/v1/camera-shadow/evaluate`。
- 复用 `evaluate_camera_fusion()` 生成 decision/camera_event/clip_plan。
- 可选 `image_base64` + `dispatch_vlm` 触发 `VLMDispatcher`；默认 dry-run 安全返回。
- 写 `camera.shadow_evaluate` audit（DB mode）。
- `tests/test_camera_shadow_pipeline.py` 新增 composite API dry-run regression。

**验证**：

```bash
python3 -m pytest tests/test_camera_shadow_pipeline.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 179 passed, 8 deselected, 1 warning
```

---

## 第 76 轮 · 2026-08-02（Composite camera shadow + Android shadow helpers）

**目标**：继续推进 Camera shadow 与 Android SleepSession 联动。

**完成内容**：

- 新增 `POST /api/v1/camera-shadow/evaluate`，组合 fusion decision、clip plan、camera_event 与 optional VLM shadow dry-run/dispatch。
- 新增 `/sleep-sessions/{id}/shadow-summary` 聚合 camera events、shadow count、kind counts、clip paths。
- Android Sleep Session TS 增加 `fetchCameraShadowSummary()` 与 `evaluateCameraShadow()`。
- API DB smoke / camera tests / Android feature tests 扩展覆盖。

**验证**：

```bash
make lint && make typecheck
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 179 passed, 8 deselected, 1 warning
```

---

## 第 75 轮 · 2026-08-02（Camera VLM shadow API）

**目标**：继续推进 Camera shadow pipeline，将 VLMDispatcher 从纯 service/test 推进到 API smoke，同时保持 shadow-mode 安全边界。

**完成内容**：

1. 新增 `POST /api/v1/camera-vlm/shadow`：
   - 输入 image_base64 / prompt / media_type / dispatch flag。
   - 使用注入的 `app.state.model_client` 调用 `VLMDispatcher`。
   - 无 model client 或 `dispatch=false` 时安全 dry-run，返回 `dispatched=false`。
2. Audit：
   - 写 `camera.vlm_shadow_dispatch`（DB mode）。
3. Tests：
   - `tests/test_camera_shadow_pipeline.py` 覆盖 fake model dispatch 与 dry-run。

**验证**：

```bash
python3 -m pytest tests/test_camera_shadow_pipeline.py tests/test_camera_adapters.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 179 passed, 8 deselected, 1 warning
```

---

## 第 74 轮 · 2026-08-02（Android TS API client / feature flows）

**目标**：继续推进 Android RN/TS 层真实服务端联动，使静态 view models 具备完整 API helper，而不是只构造本地展示模型。

**完成内容**：

1. `android/src/api/client.ts`：新增 `get<T>()` / `put<T>()` / `delete<T>()`。
2. Today：`fetchTodayServerSnapshot()` 读取 `/babies/{id}/state`、`/system/health`、`/alerts`。
3. Timeline：新增 fetch/correction/soft-delete API helpers。
4. Alert Center：新增 list/deliveries/dispatch/ack/feedback helpers。
5. Sleep Session：新增 start/pause/resume/end/saveROI/fetchCameraEvents helpers。
6. Static tests 覆盖新增 API route strings。

**验证**：

```bash
python3 -m pytest tests/test_android_features.py tests/test_android_skeleton.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 179 passed, 8 deselected, 1 warning
```

---

## 第 73 轮 · 2026-08-02（Copilot confirmation APIs）

**目标**：补齐 Copilot 输出候选后的确认落库路径，推进 `APC-T027/T028/T030` 的实际 App/API 闭环。

**完成内容**：

1. Record candidate confirm：
   - `POST /api/v1/copilot/record-candidates/confirm`。
   - 将 Logger/QuickRecord candidate 转为 `ObservationEvent`。
   - 写 `copilot.record_confirm` audit。
2. Family memory confirm：
   - `POST /api/v1/copilot/family-memory/confirm`。
   - 写 FamilyKnowledge repository。
   - 写 `copilot.family_memory_confirm` audit。
3. Tests：
   - `tests/test_orchestrator.py` 覆盖两个 confirm endpoint。
   - `tests/integration/test_api_db_runtime.py` 覆盖 DB smoke。

**验证**：

```bash
make lint
make typecheck
python3 -m pytest tests/test_orchestrator.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 179 passed, 8 deselected, 1 warning
```

---

## 第 72 轮 · 2026-08-02（Health DB gray alert persistence）

**目标**：补强 `APC-T035`，让真实 DB mode 的 health check 产生持久化 gray alert，并审计 health check。

**完成内容**：

1. `DeviceHealthMonitor` 改为依赖 create-alert protocol，不再限定 InMemory repo。
2. `/api/v1/system/health/check` 在 DB mode 用 `SQLAlchemyAlertRepository` 生成 gray alerts。
3. health check 写 `system.health_check` audit。
4. API DB smoke 扩展 offline camera probe → gray alert persisted。

**验证**：

```bash
python3 -m pytest tests/test_health_api_probes.py tests/test_health_probes.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 174 passed, 8 deselected, 1 warning
```

---

## 第 71 轮 · 2026-08-02（Android Rule Engine screen）

**目标**：继续推进 Android 与 Rule Engine 联动，让家长端/真机 fallback 可直接触发 P0 规则评估，避免 LLM 生成医疗/剂量输出。

**完成内容**：

1. Android native screen：
   - `RuleEvaluationActivity.kt`。
   - Buttons: Medication safety / Triage fever / Vaccine plan / Growth check。
   - Calls `/api/v1/rules/evaluate/{domain}` through `NativeApiClient`。
   - UI 明确：Rule Engine only，No LLM dose/triage generation。
2. RN/TS helper：
   - `android/src/features/rules/ruleEvaluation.ts`。
   - `evaluateRuleDomain()` plus summary helpers。
3. App wiring：
   - MainActivity adds Rule Engine entry。
   - Manifest registers RuleEvaluationActivity。
4. Tests：
   - Native skeleton static tests cover RuleEvaluationActivity and safety statement。

**验证**：

```bash
python3 -m pytest tests/test_android_native_skeleton.py tests/test_rules_admin_api.py tests/test_android_skeleton.py tests/test_android_features.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 174 passed, 8 deselected, 1 warning
```

---

## 第 70 轮 · 2026-08-01（Rule evaluation API）

**目标**：继续推进 Rule Engine 对 App/Copilot 的服务端可调用接口，避免客户端或 Copilot 绕过 Rule Engine。

**完成内容**：

1. 新增 `POST /api/v1/rules/evaluate/{domain}`：
   - medication
   - triage
   - thresholds
   - vaccine
   - growth
2. API 只调用对应 RuleModule，不经 LLM。
3. Tests 覆盖 P0 domains 的 rule evaluation API。

**验证**：

```bash
python3 -m pytest tests/test_rules_admin_api.py tests/test_medication_rules.py tests/test_triage_threshold_rules.py tests/test_vaccine_rules.py tests/test_growth_rules.py -q
# 10 passed
```

---

## 第 69 轮 · 2026-08-01（Family Knowledge API / memory persistence）

**目标**：继续推进 `APC-T030` 的 FamilyMemory 持久化和 DB audit，补齐家庭偏好/纠错记忆的 API。

**完成内容**：

1. Repositories：
   - `server/app/memory/family_knowledge_repo.py`
   - In-memory + SQLAlchemy implementation。
   - Upsert 同 key 会 version+1。
2. API：
   - `POST /api/v1/family-knowledge`
   - `GET /api/v1/family-knowledge/{family_id}`
   - upsert 写 `family_knowledge.upsert` audit。
3. FastAPI wiring：
   - dev mode 注入 `InMemoryFamilyKnowledgeRepository`。
   - DB mode route 使用 `SQLAlchemyFamilyKnowledgeRepository`。
4. Tests：
   - `tests/test_family_knowledge_api.py`。
   - API DB smoke 改用 FamilyKnowledge API 并校验 audit。

**验证**：

```bash
python3 -m pytest tests/test_family_knowledge_api.py tests/test_memory_store.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 174 passed, 8 deselected, 1 warning
```

---

## 第 68 轮 · 2026-08-01（Sync heartbeat API / Android pending report）

**目标**：继续推进 Android pending_sync 可观测性，补齐服务端 sync_state heartbeat API。

**完成内容**：

1. Sync state repositories：
   - `server/app/sync/state_repo.py`
   - `server/app/sync/sqlalchemy_state_repo.py`
2. Sync API：
   - `POST /api/v1/sync/heartbeat`
   - `GET /api/v1/sync/state/{client_id}`
   - Mutating heartbeat 写 `sync.heartbeat` audit。
3. App wiring：
   - FastAPI dev mode 注入 `InMemorySyncStateRepository`。
   - DB mode 自动使用 `SQLAlchemySyncStateRepository`。
4. Android：
   - `pending_sync_drain.ts` drain 后可调用 `/api/v1/sync/heartbeat` 上报 pending count。
5. Tests：
   - `tests/test_sync_state_api.py`。
   - API DB smoke 覆盖 sync heartbeat。

**验证**：

```bash
python3 -m pytest tests/test_sync_state_api.py tests/test_android_skeleton.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 172 passed, 8 deselected, 1 warning
```

---

## 第 67 轮 · 2026-08-01（Android native login + save/drain）

**目标**：继续推进 `APC-T046/T047/T048`，让 native Android fallback 可以完成登录、设备注册、token 加密保存，并让 Quick Record 使用 session 上下文。

**完成内容**：

1. `LoginActivity.kt`：
   - 输入 API base URL / family_id / display name / secret / optional baby_id。
   - 调用 `/api/v1/auth/login`。
   - 调用 `/api/v1/auth/devices/register` 注册 phone。
   - 使用 `SecureSessionStore` 加密保存 token/session。
2. `MainActivity.kt`：新增 Login 入口。
3. `QuickRecordActivity.kt`：
   - 保存 feeding 时优先使用 SecureSession 中的 family/baby/user/device。
   - 新增 “Save and trigger drain” 立即调度 BackgroundDrainScheduler。
4. Static tests 覆盖 LoginActivity API routes / SecureSessionStore / QuickRecord trigger drain。

**验证**：

```bash
python3 -m pytest tests/test_android_native_skeleton.py tests/test_android_skeleton.py tests/test_android_features.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 171 passed, 8 deselected, 1 warning
```

**用户下一步（非阻塞本轮）**：

```bash
cd android/android && ./gradlew assembleDebug
```

---

## 第 66 轮 · 2026-08-01（Android native screen actions）

**目标**：继续推进 Android native fallback screens，不只读服务端数据，也能执行核心动作。

**完成内容**：

1. `NativeApiClient` 新增 `putJsonResult()`。
2. `AlertCenterActivity`：
   - refresh alerts 后解析第一条 alert id。
   - 新增 “Submit useful feedback” 调用 `/api/v1/alerts/{id}/feedback`。
3. `SleepSessionActivity`：
   - 新增 “Save default ROI” 调用 `PUT /api/v1/sleep-sessions/{id}/roi`。
   - 新增 “Refresh camera events” 调用 `GET /api/v1/sleep-sessions/{id}/camera-events`。
4. Static tests 覆盖 feedback/ROI/camera-events API route strings。

**验证**：

```bash
make lint
make typecheck
python3 -m pytest tests/test_android_native_skeleton.py tests/test_android_skeleton.py tests/test_android_features.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 171 passed, 8 deselected, 1 warning
```

---

## 第 65 轮 · 2026-08-01（Android native screens server refresh）

**目标**：继续推进 Android native fallback screens，从纯本地展示升级为可直接读服务端 API。

**完成内容**：

1. `NativeApiClient`：新增 `getJson()` 和 `postJsonResult()`，返回 status/body。
2. `TodayActivity`：可刷新 `/api/v1/system/health`。
3. `TimelineActivity`：可刷新 `/api/v1/events?baby_id=...`。
4. `AlertCenterActivity`：可刷新 `/api/v1/alerts?family_id=...`，并保留 ack drain。
5. `SleepSessionActivity`：支持 start/pause/resume/end 服务端 API 调用，并解析 session id。
6. Static tests 扩展 native screen API route checks。

**验证**：

```bash
python3 -m pytest tests/test_android_native_skeleton.py tests/test_android_skeleton.py tests/test_android_features.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 171 passed, 8 deselected, 1 warning
```

**用户下一步（非阻塞本轮）**：

```bash
cd android/android && ./gradlew assembleDebug
```

---

## 第 64 轮 · 2026-08-01（mmWave live MQTT worker）

**目标**：继续推进 `APC-T040`，从 mmWave ingest API 补齐 live MQTT worker/CLI。

**完成内容**：

1. Shared ingest service：
   - `server/app/mmwave/ingest_service.py`
   - API 与 worker 共用 parse → sensor_event → optional observation_event 流程。
2. Live MQTT worker：
   - `server/app/mmwave/worker.py`
   - `MMWaveMQTTWorker` 使用 aiomqtt 订阅 configured topics。
   - 支持 snapshot：received_count/persisted_sensor_count/persisted_observation_count/last_signal_type/last_error。
3. CLI / Make target：
   - `server/scripts/run_mmwave_worker.py`
   - `make run-mmwave-worker`
   - 支持 env：`PARENTING_MMWAVE_BABY_ID` / `PARENTING_MMWAVE_FAMILY_ID`。
4. Tests：
   - `tests/test_mmwave_ingest_service.py`。

**验证**：

```bash
python3 -m pytest tests/test_mmwave_ingest_service.py tests/test_mmwave_api.py tests/test_mmwave_parser.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 171 passed, 8 deselected, 1 warning
```

**状态说明**：

- `APC-T040` 仍保持 BLOCKED，等待真实 MQTT broker/device soak。

---

## 第 63 轮 · 2026-08-01（Camera fusion API + clip plan）

**目标**：继续推进 `APC-T039`，把 pure FusionStateMachine/ClipRecorder 推进到 API + DB smoke。

**完成内容**：

1. Camera fusion API：
   - `POST /api/v1/camera-fusion/evaluate`
   - 输入 sleep active、camera kind/confidence、mmWave abnormal event。
   - 输出 decision、clip_plan、camera_event。
2. Shadow camera event：
   - 多信号 shadow candidate 自动写 `camera_event`。
   - `ClipRecorder` 生成 `runtime/media/clips/<session_id>.mp4` plan。
3. Tests：
   - `tests/test_camera_adapters.py` 覆盖 fusion API dev path。
   - `tests/integration/test_api_db_runtime.py` 覆盖 DB fusion/audit path。

**验证**：

```bash
python3 -m pytest tests/test_camera_adapters.py tests/test_camera_shadow_pipeline.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 169 passed, 8 deselected, 1 warning
```

**状态说明**：

- `APC-T039` 仍保持 BLOCKED，等待真实 VLM/media/device shadow 验收。

---

## 第 62 轮 · 2026-08-01（Dev E2E substitutes + security status）

**目标**：补强 E2E 自动化替代测试，减少后续手工验证压力，并根据已通过的 security/db audit 前置解除 `APC-T058`。

**完成内容**：

1. MVP feeding dev E2E substitute：
   - `tests/e2e/test_mvp_feeding_dev_roundtrip.py`
   - API event write → normalization → DerivedBabyState API。
2. Red alert API E2E substitute：
   - `tests/e2e/test_red_alert_api_flow.py`
   - Alert create → dispatch → ack → cancel delivery receipts → feedback。
3. Audit correctness fix：
   - `alert.dispatch` / `alert.cancel_channels` 在 dev MemoryAuditSink 也记录，满足 mutating operation audit rule。
4. 状态同步：
   - `APC-T058` → DONE。

**验证**：

```bash
make e2e-fake-test
# 3 passed
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 168 passed, 8 deselected, 1 warning
```

---

## 第 61 轮 · 2026-08-01（Android native core screens）

**目标**：继续推进 Android P0 UI，从单一 shell 页面扩展到 Today/Timeline/Alert/Sleep Session native fallback screens，提升真机可验收面积。

**完成内容**：

1. Native screens：
   - `TodayActivity.kt`：pending sync / last drain summary / navigation。
   - `TimelineActivity.kt`：local pending events timeline。
   - `AlertCenterActivity.kt`：local alert ack action drain。
   - `SleepSessionActivity.kt`：calls `/api/v1/sleep-sessions` through NativeApiClient。
2. MainActivity launcher：
   - Today / Quick Record / Timeline / Alert Center / Sleep Session / Pending Sync / API Settings / Critical Alert Demo。
3. Manifest：
   - 注册 Today/Timeline/AlertCenter/SleepSession activities。
4. Static tests：
   - `tests/test_android_native_skeleton.py` 覆盖新 screens 和 navigation targets。

**验证**：

```bash
make lint
make typecheck
python3 -m pytest tests/test_android_native_skeleton.py tests/test_android_skeleton.py tests/test_android_features.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 166 passed, 8 deselected, 1 warning
```

**用户下一步（非阻塞本轮）**：

```bash
cd android/android && ./gradlew assembleDebug
```

---

## 第 60 轮 · 2026-08-01（Android background drain / mmWave events list）

**目标**：继续加速推进 Android 离线同步闭环和 mmWave API 可观测性。

**完成内容**：

1. Android background drain：
   - `NativeApiClient.kt` 保持 native fallback POST client。
   - 新增 `ApiSettingsStore.kt` / `ApiSettingsActivity.kt`：配置 API base URL，查看 last drain summary，手动 trigger drain。
   - 新增 `BackgroundDrainScheduler.kt` / `BackgroundDrainJobService.kt`：JobScheduler 定期 drain pending events 和 alert ack actions。
   - 新增 `BootReceiver.kt`：开机恢复 periodic drain。
   - `MainApplication` 自动 schedule periodic drain。
   - `MainActivity` 增加 API Settings / Drain 入口。
2. mmWave list API：
   - `GET /api/v1/mmwave/devices/{device_id}/events`，支持 dev in-memory 和 DB repository。
   - API DB smoke 增加 mmWave list 断言。
3. Tests：
   - Android native skeleton static tests 覆盖 JobService/JobScheduler/BootReceiver/API settings。
   - mmWave API test 覆盖 ingest 后 list。

**验证**：

```bash
python3 -m pytest tests/test_mmwave_api.py tests/test_android_native_skeleton.py tests/test_android_skeleton.py tests/test_android_features.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 166 passed, 8 deselected, 1 warning
```

**用户下一步（非阻塞本轮）**：

```bash
cd android/android && ./gradlew assembleDebug
```

---

## 第 59 轮 · 2026-08-01（Android native API drains）

**目标**：继续推进 Android 离线记录与告警确认闭环，从 TS bridge contract 进一步推进到 native fallback screens 可调用的 Kotlin drainers。

**完成内容**：

1. Native API client：
   - `NativeApiClient.kt`：最小 HttpURLConnection POST JSON client，支持 Bearer token。
   - `NativeDrainResult`。
2. Pending event native drain：
   - `PendingSyncDrainer.kt`：读取 `LocalEventStore.pending()`，POST `/api/v1/events`，成功后 `markSynced()`。
3. Alert ack native drain：
   - `AlertAckDrainer.kt`：读取 `AlertActionReceiver.drainLocalActions()`，POST `/api/v1/alerts/{id}/ack`，失败时重新记录本地 action。
4. Native UI：
   - `PendingEventsActivity` 增加“Drain pending to server”按钮，默认 emulator API `http://10.0.2.2:8000`。
5. Static tests：
   - `tests/test_android_native_skeleton.py` 覆盖 native client/drainers/action drain。

**验证**：

```bash
make lint
make typecheck
python3 -m pytest tests/test_android_native_skeleton.py tests/test_android_skeleton.py tests/test_android_features.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 166 passed, 8 deselected, 1 warning
```

**用户下一步（非每轮必需）**：

```bash
cd android/android && ./gradlew assembleDebug
```

---

## 第 58 轮 · 2026-08-01（Android pending sync / alert ack drains）

**目标**：继续推进 Android 端离线记录与告警确认闭环，补齐 native bridge 上层的 drain 逻辑。

**完成内容**：

1. Pending event drain：
   - `android/src/sync/pending_sync_drain.ts`
   - 从 `NativeLocalEventBridge.pending()` 读取本地 pending events。
   - POST `/api/v1/events` 成功后调用 `markSynced()`。
   - 失败事件保留 pending，并返回 attempted/synced/failed/failedEventIds。
2. Alert ack drain：
   - `android/src/notification/ack_drain.ts`
   - 从 native alert bridge `drainLocalActions()` 读取本地 ack/dismiss。
   - ack action 调用 `/api/v1/alerts/{alert_id}/ack`。
   - 成功后 `stopLocalFallback(alert_id)`。
3. Static tests：
   - `tests/test_android_skeleton.py` 覆盖 pending sync drain。
   - `tests/test_android_features.py` 覆盖 alert ack drain。

**验证**：

```bash
python3 -m pytest tests/test_android_skeleton.py tests/test_android_features.py tests/test_android_native_skeleton.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 166 passed, 8 deselected, 1 warning
```

**状态说明**：

- `APC-T047/T048/T052` 仍等待 Android build/device/PowerSync/Notifee/FCM 验收，但 app 侧 bridge+drain 逻辑已补齐。

---

## 第 57 轮 · 2026-08-01（Camera/mmWave ingest APIs）

**目标**：继续推进 `APC-T038/T039/T040`，从 DB repository smoke 继续推进到 API ingest 层。

**完成内容**：

1. mmWave ingest API：
   - `server/app/mmwave/api/routes.py`
   - `POST /api/v1/mmwave/frames`：parse radar frame → sensor event → DB repository；传入 baby/family 时创建 sensor ObservationEvent。
   - 写 `mmwave.frame_ingest` audit。
2. Camera event API：
   - `POST /api/v1/camera-events`
   - `GET /api/v1/sleep-sessions/{session_id}/camera-events`
   - DB mode 写 `camera_event`，dev mode 写 app.state in-memory records。
   - 写 `camera_event.create` audit。
3. API DB smoke：
   - `tests/integration/test_api_db_runtime.py` 扩展 mmWave frame ingest、sensor observation、camera event create/list。
4. Unit/dev API tests：
   - `tests/test_mmwave_api.py`
   - `tests/test_camera_adapters.py` 扩展 camera event route。

**验证**：

```bash
python3 -m pytest tests/test_mmwave_api.py tests/test_camera_adapters.py tests/test_more_db_repository_adapters.py tests/test_mmwave_parser.py tests/test_camera_shadow_pipeline.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 166 passed, 8 deselected, 1 warning
```

**状态说明**：

- `APC-T038/T039/T040` 仍保持 BLOCKED，等待真实 camera/mmWave hardware/MQTT/VLM 验收。

---

## 第 56 轮 · 2026-08-01（Camera/mmWave DB repository smoke）

**目标**：继续推进 `APC-T038/T039/T040`，将 camera/mmWave 从 pure/static/mock 推进到 SQLAlchemy repository DB smoke。

**完成内容**：

1. mmWave DB repository：
   - `server/app/mmwave/sqlalchemy_sensor_event_repo.py`
   - 支持 `SensorEventCandidate` → `sensor_event`。
   - 支持 `list_by_device()`。
2. Camera DB repository：
   - `server/app/camera/sqlalchemy_camera_event_repo.py`
   - 支持 `CameraEventRecord` → `camera_event`。
   - 支持 `list_by_session()` / `list_by_camera()`。
3. Integration：
   - `tests/integration/test_db_repository_adapters.py` 扩展 sensor_event/camera_event DB smoke。
4. Static repository tests：
   - `tests/test_more_db_repository_adapters.py` 覆盖新 adapters。

**验证**：

```bash
python3 -m pytest tests/test_more_db_repository_adapters.py tests/test_mmwave_parser.py tests/test_camera_shadow_pipeline.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 164 passed, 8 deselected, 1 warning
```

**状态说明**：

- `APC-T038/T039/T040` 仍保持 BLOCKED，等待真实 RTSP/ISAPI/Fregata/MQTT/VLM/device 验收。

---

## 第 55 轮 · 2026-08-01（Scheduler worker + Restore drill planner）

**目标**：继续推进 `APC-T036/T044`，补齐长期 scheduler worker 基础与 restore drill 计划能力。

**完成内容**：

1. Scheduler worker：
   - `server/app/scheduler/worker.py`
   - `PeriodicSchedulerWorker` 支持 start/stop/run_once/interval loop。
   - FastAPI lifespan 注册 scheduler worker，默认 `run_on_start=False`，避免启动时产生提醒/告警副作用。
   - Snapshot 记录 run_count / last run / errors / results。
2. Restore drill：
   - `server/app/backup/restore_drill.py`
   - `RestoreDrillPlanner` 生成 `pg_restore` command。
   - `BackupManifest` 记录 pg dump/media archive/verification steps。
   - `make restore-dry-run`。
   - `docs/BACKUP_RESTORE_RUNBOOK.md`。
3. Tests：
   - `tests/test_scheduler_worker.py`
   - `tests/test_backup_tasks.py` 扩展 restore drill plan/manifest。

**验证**：

```bash
make lint
make typecheck
python3 -m pytest tests/test_scheduler_worker.py tests/test_scheduler_api.py tests/test_backup_tasks.py -q
make restore-dry-run
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 164 passed, 8 deselected, 1 warning
```

**状态说明**：

- `APC-T036` 仍等待 T022 生产规则审查与长期运行验收。
- `APC-T044` 仍等待真实 pg_dump/NAS/restore drill。

---

## 第 54 轮 · 2026-08-01（Sleep / Media / Export DB API smoke）

**目标**：继续推进 `APC-T037/T042/T043`，补齐 DB-backed API runtime 与 audit 覆盖。

**完成内容**：

1. Sleep Session DB API：
   - `SQLAlchemySleepSessionRepository` 支持 start/pause/resume/end/set_roi。
   - Camera/Sleep API DB mode 自动切换 SQLAlchemy repo。
   - Mutating routes 写 `sleep_session.*` audit。
2. Media DB persistence：
   - Media upload DB mode 写 `media_asset`。
   - Media read 支持从 DB metadata 恢复 record 并读取加密文件。
   - Mutating route 写 `media.upload` audit。
3. Export API：
   - `POST /api/v1/exports/summary`。
   - `GET /api/v1/exports/{export_id}`。
   - 写 `export.summary` audit。
4. API DB smoke：
   - 扩展 sleep session flow、media upload/read、export create/read，并校验 audit actions。

**验证**：

```bash
make lint
make typecheck
python3 -m pytest tests/test_media_storage.py tests/test_sleep_session.py tests/test_export_api.py tests/test_export_service.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 161 passed, 8 deselected, 1 warning
```

**状态说明**：

- `APC-T037/T042/T043` 等待用户 Mac `make api-db-smoke-test` 复验后解除主要 DB/audit 阻塞。

---

## 第 53 轮 · 2026-08-01（Scheduler API + APC-T035 accepted）

**目标**：根据用户 `make api-health-smoke` 真实环境通过解除 `APC-T035`，并继续推进 `APC-T036` 的可操作 API。

**完成内容**：

1. 状态同步：
   - `APC-T035`：BLOCKED → DONE
2. Scheduler API：
   - `GET /api/v1/scheduler/jobs`
   - `POST /api/v1/scheduler/jobs/{job_name}/trigger`
   - `POST /api/v1/scheduler/trigger-all`
3. App wiring：
   - 初始化 `SchedulerRunner`。
   - 注册 `MorningBriefJob`、`SupplementReminderJob`、`HealthCheckJob`、`VaccineDueJob`。
4. Audit：
   - 手动 trigger 写入 `scheduler.trigger` / `scheduler.trigger_all` audit。
5. Tests：
   - `tests/test_scheduler_api.py` 覆盖 job list/trigger/trigger-all/404。

**验证**：

```bash
python3 -m ruff check server/app/main.py server/app/scheduler/api/routes.py tests/test_scheduler_api.py
python3 -m pytest tests/test_scheduler_api.py tests/test_scheduler_jobs.py -q
python3 -m mypy server/app
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 159 passed, 8 deselected, 1 warning
```

**状态说明**：

- `APC-T036` 仍保持 BLOCKED，等待 T022 生产规则审查与长期 worker/定时运行验收。

---

## 第 52 轮 · 2026-08-01（FastAPI local API runbook / smoke targets）

**目标**：修复用户指出的 FastAPI 服务启动说明缺失问题，并提供可自动验证的 API health smoke。

**完成内容**：

1. 新增 `docs/RUNBOOK_LOCAL_API.md`：
   - Terminal 1：`make infra-up` / `make db-migrate`。
   - Terminal 2：`make run-api` 前台启动 uvicorn。
   - Terminal 3：`make api-health-smoke` 或 curl。
   - 常见错误解释：`curl: (7)` 表示服务未启动。
2. Makefile：
   - `make run-api` alias。
   - `make api-health-smoke`：检查一个已经运行在 8000 的服务；不可达时打印明确启动步骤。
   - `make api-server-smoke-test`：临时启动 uvicorn 到 8766，检查 health endpoints 后自动关闭。
3. `server/scripts/run_dev.sh`：
   - 输出 DB/PowerSync env 与 API URL。
   - 提示另开终端执行 `make api-health-smoke`。
   - 仅在 DB URL 存在时自动 `db-migrate`。

**验证**：

```bash
make lint
make typecheck
make api-server-smoke-test
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
```

---

## 第 51 轮 · 2026-08-01（System health probes / check API）

**目标**：继续推进 `APC-T035`，从 MockHealthProbe 扩展为真实服务探针和系统健康检查 API。

**完成内容**：

1. Real probes：
   - `server/app/health/probes/db.py`：SQLAlchemy `SELECT 1` database probe。
   - `server/app/health/probes/tcp.py`：TCP port probe，用于 MQTT/设备端口。
   - `server/app/health/probes/http.py`：HTTP endpoint probe。
   - `server/app/health/probes/powersync.py`：复用 `probe_powersync()` 的 PowerSync liveness probe。
2. App wiring：
   - 默认注册 MQTT TCP probe。
   - DB mode 注册 database probe。
   - `PARENTING_POWERSYNC__URL` 存在时注册 PowerSync probe。
3. API：
   - `/api/v1/system/health` 返回 latest `device_health` snapshot 和 degraded 状态。
   - `POST /api/v1/system/health/check` 手动运行 probes，offline 时沿用 DeviceHealthMonitor 生成 gray alert。
4. Tests：
   - `tests/test_health_probes.py`
   - `tests/test_health_api_probes.py`

**验证**：

```bash
make lint
make typecheck
python3 -m pytest tests/test_health_probes.py tests/test_health_api_probes.py tests/test_app_health_observability.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 157 passed, 8 deselected, 1 warning
```

**状态说明**：

- `APC-T035` 仍保持 BLOCKED，等待用户 Mac 真实 `system/health/check` 环境复验后解除。

---

## 第 50 轮 · 2026-08-01（Android Quick Record native offline write）

**目标**：继续推进 `APC-T047/T048`，在 native Android shell 中提供可验证的本地离线写入入口，而不仅是 TypeScript view model/static flow。

**完成内容**：

1. Native Quick Record：
   - `QuickRecordActivity.kt`：输入奶量并保存 feeding event 到 `LocalEventStore.insertPending()`。
   - `PendingEventsActivity.kt`：显示 pending sync 数量和最近 pending events。
   - `MainActivity.kt`：增加 Quick Record / Pending Sync / Critical Alert Demo 入口。
2. Manifest：
   - 注册 `QuickRecordActivity` 与 `PendingEventsActivity`。
3. Static tests：
   - `tests/test_android_native_skeleton.py` 覆盖 QuickRecordActivity、PendingEventsActivity、LocalEventStore insertPending 和 main launcher route。

**验证**：

```bash
make lint
make typecheck
python3 -m pytest tests/test_android_native_skeleton.py tests/test_android_skeleton.py tests/test_android_features.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 154 passed, 8 deselected, 1 warning
```

**用户下一步**：

```bash
cd projects/AI-Parenting-Copilot/android/android
./gradlew assembleDebug
```

---

## 第 49 轮 · 2026-08-01（Android secure session + native pending event store）

**目标**：在用户确认 `assembleDebug` 成功后，解除 `APC-T045` 并继续推进 `APC-T046/T047` 的 native auth/session 与 local pending event store。

**完成内容**：

1. 状态同步：
   - `APC-T045` → DONE
2. Native secure session：
   - `SecureSessionStore.kt`：Android Keystore AES/GCM encrypted token storage，保存 family/user/baby/device/role metadata。
   - `native_secure_session.ts`：RN bridge contract。
3. Native pending event store：
   - `LocalObservationEvent.kt`。
   - `LocalEventStore.kt`：SQLiteOpenHelper table `observation_event_local`，支持 insertPending / pending / markSynced / pendingCount。
   - `native_sqlite_bridge.ts`：RN bridge contract。
4. Static tests：
   - Android native skeleton tests 增加 Keystore、SQLite pending_sync 和 TS bridge 断言。

**验证**：

```bash
make lint
make typecheck
python3 -m pytest tests/test_android_native_skeleton.py tests/test_android_skeleton.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 154 passed, 8 deselected, 1 warning
```

**用户下一步**：

```bash
cd projects/AI-Parenting-Copilot/android/android
./gradlew assembleDebug
```

若通过，可推进 `APC-T046/T047` 状态；若失败，先修 native compile。

---

## 第 48 轮 · 2026-08-01（Android Gradle bootstrap + notification status unlock）

**目标**：修复用户本地 `./gradlew assembleDebug` 缺失问题，并根据用户本地 API/test 复验通过解除 notification dispatch/cancel 主链路阻塞。

**完成内容**：

1. 状态同步：
   - `APC-T032` → DONE
   - `APC-T033` → DONE
   - `APC-T034` → DONE
2. Android Gradle bootstrap：
   - 新增 `android/android/gradlew`。
   - 新增 `android/android/gradlew.bat`。
   - 新增 `android/android/gradle/wrapper/gradle-wrapper.properties`。
   - 新增 `make android-native-build`。
   - 更新 Android README / package script / `.gitignore`。
3. Static tests：
   - `tests/test_android_native_skeleton.py` 断言 `gradlew` 存在且可执行、wrapper properties 存在且版本匹配。

**验证**：

```bash
make lint
make typecheck
python3 -m pytest tests/test_android_native_skeleton.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 152 passed, 8 deselected, 1 warning
```

**用户下一步**：

```bash
cd projects/AI-Parenting-Copilot/android/android
./gradlew assembleDebug
```

---

## 第 47 轮 · 2026-08-01（Android native critical alert fallback）

**目标**：继续推进 Android 告警端能力，在 TS 静态逻辑基础上补齐 native full-screen fallback skeleton，为后续真机/Notifee/FCM 验收做准备。

**完成内容**：

1. Native Kotlin files：
   - `AlertPayload.kt`：trigger-only payload，仅 `alert_id/level/type`。
   - `CriticalAlertActivity.kt`：showWhenLocked/turnScreenOn full-screen alert UI，只展示 trigger metadata，不展示 evidence。
   - `AlertActionReceiver.kt`：记录本地 ack/dismiss action，供后续 sync/API drain。
   - `NotificationHelper.kt`：创建 critical/default channels，构建 fullScreen PendingIntent。
2. Android Manifest：
   - 注册 `CriticalAlertActivity` 与 `AlertActionReceiver`。
3. TS bridge contract：
   - `android/src/notification/native_bridge.ts`。
4. Static tests：
   - `tests/test_android_native_skeleton.py` 扩展 native full-screen files / trigger-only / channel importance / bridge 断言。

**验证**：

```bash
make lint
make typecheck
python3 -m pytest tests/test_android_native_skeleton.py tests/test_android_features.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 152 passed, 8 deselected, 1 warning
```

**状态说明**：

- `APC-T052` 继续 BLOCKED，等待真实 Android toolchain/device/FCM/Notifee permission 验收。

---

## 第 46 轮 · 2026-08-01（Notification cancel receipts + APC-T029 accepted）

**目标**：根据用户本地复验通过结果解除 `APC-T029`，并继续推进 `APC-T033/T034` 的 ack 后 cancel 与 delivery receipt 闭环。

**完成内容**：

1. 状态同步：
   - `APC-T029`：BLOCKED → DONE
2. Notification cancel：
   - `NotificationOrchestrator.cancel(alert)` 调用所有适用通道的 `cancel()` 并持久化 `status=cancelled` delivery receipts。
   - `POST /api/v1/alerts/{alert_id}/ack` ack 后自动 cancel channels。
   - 新增 `GET /api/v1/alerts/{alert_id}/deliveries`。
   - DB mode 写入 `alert.cancel_channels` audit。
3. 测试增强：
   - Unit：cancel 写入 channel cancellation receipts。
   - API dev：dispatch + ack + deliveries 包含 cancelled。
   - API DB smoke：dispatch/ack/deliveries/audit 包含 `alert.cancel_channels`。

**验证**：

```bash
make lint
make typecheck
python3 -m pytest tests/test_notification_orchestrator.py tests/test_alert_api.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 151 passed, 8 deselected, 1 warning
```

**状态说明**：

- `APC-T033/T034` 仍保持 BLOCKED，等待用户 Mac `api-db-smoke-test` 复验和真实 FCM/TTS/设备通道接入。

---

## 第 45 轮 · 2026-08-01（Notification adapters + DB delivery dispatch）

**目标**：继续推进 `APC-T032/T033`，在无真实 FCM/TTS 凭证的前提下补齐安全默认通道 adapter、dispatch API 与 DB delivery receipt 持久化。

**完成内容**：

1. Notification adapters：
   - `server/app/notification/channels/fcm.py`
   - `server/app/notification/channels/mac_speaker.py`
   - `server/app/notification/channels/app_fullscreen.py`
   - `server/app/notification/channels/camera_speaker.py`
   - `server/app/notification/channel_factory.py`
2. Alert dispatch API：
   - `POST /api/v1/alerts/{alert_id}/dispatch`
   - DB mode 使用 `SQLAlchemyDeliveryRepository` 写入 `alert_delivery`。
   - Dev mode 使用 `InMemoryDeliveryRepository`。
3. Tests：
   - FCM trigger payload 只含 `alert_id/level/type`，不含 evidence/recommended_action。
   - Default channels safe dry-run regression。
   - API DB smoke 扩展 red alert dispatch → 4 channel receipts + `alert.dispatch` audit。

**验证**：

```bash
make lint
make typecheck
python3 -m pytest tests/test_notification_channels.py tests/test_notification_orchestrator.py tests/test_alert_api.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 150 passed, 8 deselected, 1 warning
```

**状态说明**：

- `APC-T032/T033` 仍保持 BLOCKED，等待用户 Mac `api-db-smoke-test` 复验与真实 FCM/TTS/设备凭证接入。

---

## 第 44 轮 · 2026-08-01（Dose Interceptor DB audit + status unlock）

**目标**：基于用户确认 DB-backed Memory/Orchestrator 复验通过，解除相关任务阻塞，并继续推进 `APC-T029` 的真实 `audit_log` 写入。

**完成内容**：

1. 任务状态同步：
   - `APC-T020` Medication Rule Domain → DONE
   - `APC-T021` Triage / Threshold Rules → DONE
   - `APC-T026` Memory Store M1-M5 / Local RAG adapter → DONE
   - `APC-T027` Copilot Base / Registry / Logger Copilot → DONE
   - `APC-T028` Orchestrator / Intent Router / Context Builder / Output Guard → DONE
2. Dose Interceptor DB audit：
   - 新增 `server/app/observability/sqlalchemy_audit_sink.py`。
   - Orchestrator API DB mode 注入 `SQLAlchemyAuditSink(db_session)`。
   - `tests/integration/test_api_db_runtime.py` 增加 `DoseInterceptor().intercept_and_audit()` 写入 `audit_log` 并校验 `dose_intercept` action。

**验证**：

```bash
python3 -m ruff check server/app/observability/sqlalchemy_audit_sink.py server/app/orchestrator/api/routes.py tests/integration/test_api_db_runtime.py
python3 -m mypy server/app
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 148 passed, 8 deselected, 1 warning
```

**状态说明**：

- `APC-T029` 仍保持 BLOCKED，等待用户 Mac `make api-db-smoke-test` 复验真实 DB audit 后解除。

---

## 第 43 轮 · 2026-07-31（PowerSync validation accepted）

**目标**：根据用户“全部通过”结果解除 `APC-T012` 的 PowerSync liveness/config 验收阻塞。

**状态变更**：

- `APC-T012`：BLOCKED → DONE

**依据**：

- 用户 Mac 已执行并确认 `make powersync-smoke-test`、`make db-integration-test`、`make api-db-smoke-test`、`make worker-db-smoke-test`、`make test` 全部通过。

**后续**：

- 新增 DB-backed Memory / Orchestrator context 已推送，下一轮需要用户复验 `make api-db-smoke-test` 与 `make test` 后解除 `APC-T026/T027/T028` 的主要阻塞。

---

## 第 42 轮 · 2026-07-31（DB-backed Memory / Orchestrator context）

**目标**：继续推进 `APC-T026/T027/T028`，把 Copilot context 从纯 in-memory 扩展为 PostgreSQL-backed M1-M5 memory snapshot，并修正 Logger Copilot 与 Normalization parser 不一致的问题。

**完成内容**：

1. DB-backed MemoryStore：
   - `server/app/memory/sqlalchemy_store.py`
   - M1 hard facts：baby profile、age_days、weight、sex、vaccine_region、allergies。
   - M2 family prefs：`family_knowledge`。
   - M3 behavior baseline：`derived_baby_state.snapshot`。
   - M4 short context：近 72h event count/type summary。
   - M5 correction memory：`family_knowledge` correction 前缀 + optional Local RAG。
2. Local RAG thin adapter：
   - `server/app/memory/local_rag.py`
   - 接受工厂 `_infra.network.local_rag.RAGStore` 兼容 search store，不复制实现。
3. Orchestrator DB memory 注入：
   - `ContextBuilder` 支持 sync/async memory store。
   - `/api/v1/copilot/query` DB mode 下使用 `SQLAlchemyMemoryStore`。
4. Logger parser 一致性：
   - `LoggerCopilot` 复用 `normalization.parsers.voice.parse_voice_text()`，支持“奶 80 毫升”等常见顺序。
5. 测试增强：
   - `tests/test_memory_store.py` 增加 Local RAG adapter regression。
   - `tests/test_logger_copilot.py` 增加 parser word order regression。
   - `tests/integration/test_api_db_runtime.py` 增加 DB memory snapshot smoke。

**验证**：

```bash
make lint
make typecheck
python3 -m pytest tests/test_memory_store.py tests/test_logger_copilot.py tests/test_orchestrator.py -q
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 148 passed, 8 deselected, 1 warning
```

**状态同步**：

- `APC-T026/T027/T028` 保持 BLOCKED，说明已更新为“实现完成，等待用户 Mac DB/API smoke 复验”。

---

## 第 41 轮 · 2026-07-31（Worker validation accepted + PowerSync smoke target）

**目标**：根据用户“验证通过”结果同步任务状态，并继续推进下一阻塞项 `APC-T012` PowerSync 复验入口。

**完成内容**：

1. 状态解除：
   - `APC-T011` → DONE
   - `APC-T013` → DONE
   - `APC-T014` → DONE
   - `APC-T015` → DONE
   - `APC-T016` → DONE
   - `APC-T017` → DONE
2. 新增 PowerSync probe：
   - `server/app/sync/service/powersync_probe.py`
   - `tests/test_powersync_probe.py`
   - `tests/integration_powersync/test_powersync_service.py`
   - `make powersync-smoke-test`
3. PowerSync smoke 覆盖：
   - 默认探测 docker compose `.env.example` 暴露的 `http://127.0.0.1:9081/probes/liveness`。
   - 校验 deploy/app PowerSync sync config 中包含 core tables 与 soft-delete 条件。
   - 无本地服务的沙盒环境自动 skip；用户 Mac `infra-up` 后预期 liveness test 通过。

**验证**：

```bash
make lint
make typecheck
make powersync-smoke-test
# sandbox: 1 passed, 1 skipped
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 146 passed, 8 deselected, 1 warning
```

**架构影响**：

- 无架构变更。
- 未自研同步引擎；仅新增 PowerSync 服务健康探测与配置静态校验。

---

## 第 40 轮 · 2026-07-31（Live worker DB smoke target）

**目标**：在用户已确认 `db-integration-test` / `api-db-smoke-test` / `make test` 通过后，继续推进真实 PG LISTEN/NOTIFY worker 验收闭环，避免只验证手动 `PendingEventProcessor`。

**完成内容**：

1. 新增独立 worker smoke：
   - `tests/integration_worker/test_event_normalization_worker.py`
   - 真实 DB 环境下启动 FastAPI app，让 lifespan 注册并启动 `PostgresEventNormalizationWorker`。
   - API 写入 feeding event 后，等待 worker 通过 `events.changed` NOTIFY 自动归一化并生成 `/api/v1/babies/{baby_id}/state`。
   - 校验 `processing_status=normalized` 与 state `feeding_24h_ml=111`。
2. 新增 Makefile target：
   - `make worker-db-smoke-test`
   - 与 `make db-integration-test` 分离，避免常规 DB adapter suite 变慢或被异步 worker 时序影响。
3. 修复 DB state source count 持久化：
   - `SQLAlchemyStateSnapshotRepository.upsert()` 将 `source_event_count` 写入 snapshot JSON，DB API 读取时不再丢失。

**验证**：

```bash
make lint
make typecheck
make worker-db-smoke-test
# sandbox no DB URL: 1 skipped, 1 warning
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 144 passed, 6 deselected, 1 warning
```

**架构影响**：

- 无架构变更。
- worker smoke 复用既有 FastAPI lifespan / WorkerRegistry / PostgreSQL trigger / NormalizationService / StateEngine。

---

## 第 39 轮 · 2026-07-31（EvidencePolicy activate idempotency）

**目标**：修复用户 Mac `make db-integration-test` 中 `evidence_policy(policy_type, region, version)` 重复激活同一 rule pack 导致唯一键冲突的问题。

**用户验证输入**：

```text
make db-integration-test
# 1 failed: duplicate key value violates unique constraint "uq_evidence_policy_version"
# Key (policy_type, region, version)=(medication, CN, cn-medication-dev-0.1.0) already exists.
```

**修复内容**：

- `server/app/rule_engine/sqlalchemy_evidence_repo.py`
  - `activate()` 先查 exact `(policy_type, region, version)`。
  - 若 exact 已是 current，则幂等返回，不再关闭当前版本再 insert。
  - 若 exact 是历史版本，则关闭其他 current，并复活/更新 exact 记录为 current。
  - 只有新版本才 insert 新行。
- `tests/integration/test_db_repository_adapters.py`
  - 在 EvidencePolicy integration test 中连续 activate 同一个 pack 两次，断言 hash 一致且 current 可读。

**验证**：

```bash
python3 -m ruff check server/app/rule_engine/sqlalchemy_evidence_repo.py tests/integration/test_db_repository_adapters.py
python3 -m mypy server/app
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 144 passed, 5 deselected, 1 warning
make db-integration-test
# sandbox no DB URL: 5 skipped, 1 warning
make api-db-smoke-test
# sandbox no DB URL: 1 skipped, 1 warning
```

**架构影响**：

- 无架构变更；保持 EvidencePolicy repository 语义，补齐幂等性。

---

## 第 38 轮 · 2026-07-31（PG worker + DB normalization/state pipeline）

**目标**：继续推进 `APC-T011/T013/T014/T016/T017`，补齐真实 PostgreSQL 事件变更后将 pending ObservationEvent 归一化并写入 DerivedBabyState 的服务端链路。

**完成内容**：

1. 新增 DB derived table store：
   - `server/app/normalization/sqlalchemy_store.py`
   - 支持 feeding/diaper/sleep/temperature/supplement P0 derived tables。
   - 按 `event_id` 使用 PostgreSQL `ON CONFLICT` 幂等 upsert，支持并发 worker/手动 drain。
2. 新增 normalization/state worker primitives：
   - `PendingEventProcessor`：扫描 `processing_status=pending` 的 `observation_event`，调用 `NormalizationService`，写 derived table，并重算 state。
   - `process_pending_events()`：事务化 drain 一批 pending events。
   - `PostgresEventNormalizationWorker`：订阅 `events.changed` channel，收到 NOTIFY 后 drain pending events。
3. FastAPI DB mode 集成：
   - `server/app/main.py` 在 DB session factory 存在时将 `PostgresEventNormalizationWorker` 注册到既有 `WorkerRegistry`。
4. State snapshot DB upsert 并发安全：
   - `SQLAlchemyStateSnapshotRepository.upsert()` 改用 PostgreSQL `ON CONFLICT`，避免 worker 并发写入 primary key 冲突。
5. 测试增强：
   - `tests/test_normalization_worker.py` 增加 derived typed-column 映射与 asyncpg URL regression。
   - `tests/integration/test_api_db_runtime.py` 扩展 DB-backed event→normalization→state smoke；沙盒无 DB 时保持 skip，用户 Mac 需复验。

**状态同步**：

- `APC-T011/T013/T014/T016/T017` 仍保持 `BLOCKED`，但状态说明已更新为“实现完成，等待用户 Mac DB/worker 复验”。

**验证**：

```bash
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 144 passed, 5 deselected, 1 warning
make db-integration-test
# sandbox no DB URL: 5 skipped, 1 warning
make api-db-smoke-test
# sandbox no DB URL: 1 skipped, 1 warning
make lint
make typecheck
make security-test
make e2e-fake-test
make shadow-test
make rules-validate
make docs-check
```

**架构影响**：

- 无新基础设施。
- 复用既有 PostgreSQL trigger channel `events.changed`、WorkerRegistry、NormalizationService、StateEngine 与 SQLAlchemy repository 边界。
- 未改变 Rule Engine / Model Gateway / Privacy / Notification Orchestrator 边界。

---

## 第 37 轮 · 2026-07-31（DB env test isolation + seed_family DB mode）

**目标**：修复用户在 `make db-integration-test` 后继续执行 `make test` 时，由 shell 中遗留 `PARENTING_DATABASE__URL` 导致 unit/dev tests 误走 PostgreSQL repo 的问题，并继续推进 DB-backed API runtime 完成度。

**用户验证输入**：

```bash
export PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting"
make db-integration-test
# 5 passed, 1 warning in 3.97s
make test
# 修复前 5 failed：unit tests 误切 DB repo，触发 baby FK 与 dev-mock health 断言失败
```

**完成内容**：

1. 测试隔离：
   - `Makefile test` 显式 `env -u PARENTING_DATABASE__URL -u PARENTING_DATABASE_URL`。
   - 新增 `tests/conftest.py`：非 `integration` 测试自动删除 DB env，直接 `pytest -m "not integration"` 也保持 dev-mock。
2. DB smoke 可执行入口：
   - 新增 `make api-db-smoke-test`，单独运行 `tests/integration/test_api_db_runtime.py`。
3. seed_family 完整化：
   - `server/scripts/seed_family.py` 支持 in-memory 与 DB-backed 双模式。
   - 有 `--database-url` 或 `PARENTING_DATABASE__URL` 时通过 `SQLAlchemyAuthRepository` 持久化 family/admin/baby。
   - 新增 `tests/test_seed_family.py` 覆盖默认 in-memory 与 `--no-baby`。
4. 依赖清理：
   - `install-dev` 改为 `uv pip install --python $(PYTHON) -e ".[dev]"`。
   - `pyproject.toml` 去除重复 `sqlalchemy[asyncio]`，保留 `sqlalchemy[asyncio]>=2.0`。

**状态变更**：

- `APC-T008`：BLOCKED → DONE
- `APC-T010`：BLOCKED/缺失状态 → DONE
- `APC-T019`：BLOCKED → DONE
- `APC-T031`：BLOCKED → DONE

**验证**：

```bash
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting" make test
# 142 passed, 5 deselected, 1 warning
make lint
# All checks passed.
make typecheck
# Success: no issues found in 153 source files
make db-integration-test
# sandbox no DB URL: 5 skipped, 1 warning
make api-db-smoke-test
# sandbox no DB URL: 1 skipped, 1 warning
make security-test
# 5 passed
make e2e-fake-test
# 1 passed
make shadow-test
make rules-validate
make docs-check
```

**架构影响**：

- 无架构变更。
- 未引入新基础设施。
- 测试策略更符合既有边界：unit/dev tests 使用 in-memory，DB coverage 仅在 `integration` marker 下运行。

---

## 第 36 轮 · 2026-07-09（User-reported bugfixes）

**目标**：处理用户指出的疑似 bug，并继续保持验证绿灯。

**修复内容**：

1. `Makefile` Alembic targets 改为 `uv run --active python -m alembic ...`，避免直接依赖 venv pip/python 行为。
2. `pyproject.toml` SQLAlchemy dependency 改为 `sqlalchemy[asyncio]>=2.0`。
3. `project_feeding` 修复 rolling 24h window 统计 bug。
4. `voice.py` P0 parser 增强中文喂奶/体温常见顺序和空格处理。
5. Orchestrator 复用单个 `CopilotRequest`，去除重复构造。
6. Vaccine/Growth/Medication Copilots 改为 lazy rule-pack loading + absolute project-root path，避免 import/constructor 阶段相对路径 I/O 副作用。
7. `request_audit.py` 修复 audit fallback record 构造语法。

**新增/增强测试**：

- feeding 24h window regression。
- voice parser common word-order regression。
- rule copilot absolute path/lazy loading regression。
- db integration URL rendering/audit tests 继续保留。

**验证**：

```bash
make docs-check
make lint
make typecheck
make test
# 140 passed, 5 deselected, 1 warning
make db-integration-test
# no DB URL: 5 skipped
make security-test
make e2e-fake-test
make shadow-test
make rules-validate
```

---

## 第 35 轮 · 2026-07-09（Context handoff consolidation）

**目标**：在上下文压缩前更新交接文档，确保下一 Agent 可接续。

**完成内容**：

- 重写 `docs/HANDOFF.md` 为最新项目级接手入口。
- 在 `docs/PROJECT_STATE.md` 添加最终 handoff checkpoint。
- 明确 Android app 位置：`projects/AI-Parenting-Copilot/android/`。
- 明确下一步优先复验：用户 Mac `make db-integration-test` 期望 `5 passed`。
- 明确 uv-first 依赖安装与 LLM 文件头规则。

**验证**：

```bash
make docs-check
# Project docs-check passed.
cd ../..
make docs-check
# Blockers: 0
```

---

## 第 34 轮 · 2026-07-09（Request-level DB audit wiring + API DB integration fix）

**问题修复**：用户 Mac `test_db_backed_auth_event_alert_state_and_rules_api` 暴露 transaction teardown 与 fixture engine 误用问题。

**完成内容**：

- 新增 `record_request_audit()`，DB mode 写入 `audit_log`，dev mode fallback MemoryAuditSink。
- Auth/Event/Alert/Rules API mutating routes 接入 request-level audit。
- API DB integration test 改为显式 AsyncEngine fixture，独立 session seed baby，并按 family_id 清理数据。
- Integration test 增加 audit rows 断言。
- 修正 TASK_BACKLOG 顶部状态索引，使已通过 DB 验收的 T003/T004/T006/T007/T009/T018 与明细一致。

**验证**：

```bash
make test
# 137 passed, 5 deselected, 1 warning
make db-integration-test
# no DB URL: 5 skipped; user Mac should run real 5 tests
```

---

## 第 33 轮 · 2026-07-09（DB-backed API runtime integration isolation fix）

**问题**：用户 Mac 执行 `make db-integration-test` 时，`test_db_backed_auth_event_alert_state_and_rules_api` 失败：

- 外层 `session` fixture 内部手动 `commit()` 导致 teardown rollback 已关闭 transaction。
- state snapshot seeding 误引用 pytest fixture function `engine`，而非 AsyncEngine 实例。

**修复**：

- 测试改为接收 `engine: AsyncEngine` fixture。
- 通过 API 创建 family/admin 后，用独立 DB session 为同一 family seed baby。
- 测试结束后按 family_id 清理相关 DB 数据。
- State snapshot seeding 使用真实 engine 创建 session。

**验证**：

```bash
make test
# 137 passed, 5 deselected, 1 warning
make db-integration-test
# no DB URL: 5 skipped; user Mac should run real 5 tests
```

---

## 第 32 轮 · 2026-07-09（DB-backed API runtime integration harness）

**目标**：为 DB-backed FastAPI runtime wiring 增加真实集成验收入口。

**完成内容**：

- 新增 `tests/integration/test_api_db_runtime.py`。
- 覆盖 request-level SQLAlchemy session middleware。
- 覆盖 Auth/Events/Alert/Rules/State API 在 DB URL 存在时走 SQLAlchemy adapters。

**验证**：

```bash
make test
# 137 passed, 5 deselected, 1 warning
make db-integration-test
# no DB URL: 5 skipped; with DB URL on Mac should run 5 real tests
```

---

## 第 31 轮 · 2026-07-09（Android native skeleton）

**目标**：明确 Android 手机端应用程序位置，并补齐最小 native Android 工程骨架。

**完成内容**：

- `android/android/` native Android skeleton。
- AndroidManifest 权限：INTERNET、POST_NOTIFICATIONS、USE_FULL_SCREEN_INTENT、VIBRATE、WAKE_LOCK。
- MainActivity/MainApplication Kotlin placeholder。
- Native modules placeholder 与 red alert Detox placeholder。
- Static tests: `tests/test_android_native_skeleton.py`。

**状态说明**：

`APC-T045/T052/T057` 仍保持 BLOCKED：真实 Gradle wrapper、RN bridge、Notifee/FCM native integration 与设备 E2E 尚未验收。

**验证**：

```bash
make test
# 137 passed, 4 deselected, 1 warning
```

---

## 第 30 轮 · 2026-07-09（DB-backed runtime repository wiring）

**目标**：继续推进从 dev/in-memory API 到 DB-backed runtime 的切换。

**完成内容**：

- `create_app()` 在配置 DB URL 时创建 async engine/session factory。
- 新增 request-level db_session middleware，成功响应 commit，错误响应 rollback。
- Auth API 在 DB mode 使用 `SQLAlchemyAuthRepository`。
- Events API 在 DB mode 使用 `SQLAlchemyEventRepository`。
- Alert API 在 DB mode 使用 `SQLAlchemyAlertRepository`。
- Rules Admin API 在 DB mode 使用 `SQLAlchemyEvidencePolicyRepository`。
- `SQLAlchemyAlertRepository` 补齐 `list_active`。

**验证**：

```bash
make test
# 134 passed, 4 deselected, 1 warning
make db-integration-test
# no DB URL: 4 skipped
```

---

## 第 29 轮 · 2026-07-09（DB integration accepted; core task unblock）

**用户验收结果**：

```bash
make infra-up
make db-migrate
make db-current
make db-integration-test
# 4 passed
```

**状态变更**：

- `APC-T003`：BLOCKED → DONE
- `APC-T004`：BLOCKED → DONE
- `APC-T006`：BLOCKED → DONE
- `APC-T007`：BLOCKED → DONE
- `APC-T009`：BLOCKED → DONE
- `APC-T018`：BLOCKED → DONE

**未解除项说明**：

`APC-T008/T010/T011/T012/T013/T014/T015/T016/T017/T019` 等仍依赖 API runtime DB wiring、PowerSync、worker、真实链路或前置任务完整验收，暂不标记 DONE。

---

## 第 28 轮 · 2026-07-09（DB integration URL password rendering fix）

**问题**：用户 Mac 执行 `make db-integration-test` 时，migration roundtrip test 仍报 `InvalidPasswordError`。虽然已改为连接应用库 `parenting`，但 SQLAlchemy URL 转字符串时默认将密码隐藏为 `***`，导致 asyncpg 实际收到错误密码。

**修复**：

- `_temp_database_urls()` 使用 `render_as_string(hide_password=False)`，保留真实密码。
- 新增 `tests/test_db_integration_url_rendering.py`，防止再次把 `***` 传给 asyncpg。

**验证**：

```bash
make test
# 134 passed, 4 deselected, 1 warning
make db-integration-test
# no DB URL: 4 skipped
```

---

## 第 27 轮 · 2026-07-09（DB integration temp database auth fix）

**问题**：用户 Mac 执行 `make db-integration-test` 时，前三个 integration tests 通过，migration roundtrip test 连接 maintenance database `postgres` 报 `InvalidPasswordError`。

**修复**：

- `_temp_database_urls()` 不再强制切换到 `postgres` maintenance database。
- 改为使用已经验证可登录的应用数据库作为 admin connection target，仍然创建独立临时 database 执行 Alembic upgrade/downgrade/upgrade。

**验证**：

```bash
make test
# 133 passed, 4 deselected, 1 warning
make db-integration-test
# sandbox without DB URL: 4 skipped
```

---

## 第 26 轮 · 2026-07-09（Media package tracking fix）

**目标**：修复用户侧 `server.app.media` import 失败的根因。

**完成内容**：

- `.gitignore` 中 `media/` 改为 `/media/`，避免递归忽略 `server/app/media/` 源码包。
- 补充 media subpackage `__init__.py`。
- 确认 `server/app/media/*` 纳入 Git 跟踪。

**验证**：

```bash
make docs-check
make lint
make typecheck
make test
make db-integration-test
make security-test
make e2e-fake-test
make shadow-test
make rules-validate
```

---

## 第 25 轮 · 2026-07-09（DB integration test harness）

**目标**：为用户下一次集中验收提供真实 PostgreSQL transaction 级验证入口。

**完成内容**：

- 新增 `tests/integration/test_db_repository_adapters.py`。
- 新增 `make db-integration-test`。
- 默认 `make test` 改为排除 `integration` marker，避免无 DB 环境误跑外部依赖测试。
- `pyproject.toml` 注册 `integration` pytest marker。

**覆盖范围**：

- Alembic upgrade head。
- Auth/Event/State/Alert/Delivery/Media/SleepSession SQLAlchemy adapters CRUD。
- EvidencePolicy activation。
- audit_log immutability trigger 拒绝 UPDATE。

**验证**：

```bash
make test
# 133 passed, 2 deselected, 1 warning
make db-integration-test
# no PARENTING_DATABASE__URL 时 2 skipped；用户 Mac DB 环境应执行真实测试
```

---

## 第 24 轮 · 2026-07-09（更多 DB-backed repository adapter skeletons）

**目标**：继续减少 BLOCKED 任务剩余工作，补充 State/EvidencePolicy/Media/Delivery/SleepSession 的 SQLAlchemy adapters。

**完成内容**：

- `SQLAlchemyStateSnapshotRepository`：derived_baby_state upsert/get。
- `SQLAlchemyEvidencePolicyRepository`：EvidencePolicy activate/get_current。
- `SQLAlchemyMediaAssetRepository`：MediaAsset metadata add/get。
- `SQLAlchemyDeliveryRepository`：alert_delivery add/list_by_alert。
- `SQLAlchemySleepSessionRepository`：SleepSession add/get。
- `tests/test_more_db_repository_adapters.py`：静态验证 adapters 使用 AsyncSession/select，并保留关键 metadata paths。

**状态说明**：

该轮不改变 task 状态：真实 PostgreSQL transaction、DB constraints 与 audit 持久化仍需用户 Mac 集中验收。

**验证**：

```bash
make docs-check && make lint && make typecheck && make test
# 133 passed, 1 warning
```

---

## 第 23 轮 · 2026-07-09（DB-backed repository adapter skeletons）

**目标**：继续减少 BLOCKED 任务剩余工作，先实现可静态验证的 SQLAlchemy DB repository adapters。

**完成内容**：

- `SQLAlchemyAuthRepository`：family/user/device/baby 基础持久化与查询。
- `SQLAlchemyEventRepository`：ObservationEvent upsert/get/list/soft_delete/correct，保留 idempotency 检查。
- `SQLAlchemyAlertRepository`：Alert create/get/ack/feedback DB adapter。
- `tests/test_db_repository_adapters.py`：静态验证 adapters 使用 AsyncSession/select，并保留幂等/软删除/ack/feedback 关键路径。

**状态说明**：

该轮不改变 task 状态：真实 PostgreSQL transaction、DB constraints 与 audit 持久化仍需用户 Mac 集中验收。

**验证**：

```bash
make docs-check && make lint && make typecheck && make test
# 130 passed, 1 warning
```

---

## 第 22 轮 · 2026-07-09（APC-T056 MVP E2E checklist + APC-T059 Shadow/Soak/Harden）

**状态变更**：

- `APC-T056`：TODO → BLOCKED（semi-automated checklist/Detox placeholder 完成；真实 Android/PowerSync E2E 待验收）
- `APC-T059`：TODO → BLOCKED（shadow harness/soak locustfile/release checklist/smoke tests 完成；真实 7 晚 shadow/soak/release checklist 待验收）

**验证**：

```bash
make docs-check && make lint && make typecheck && make test && make security-test && make e2e-fake-test && make shadow-test && make rules-validate
# 127 passed, 1 warning; security-test 5 passed; e2e-fake-test 1 passed; rule packs validated
```

---

## 第 21 轮 · 2026-07-09（APC-T011/T012/T019 PG Notify / Sync Contract / Rules Admin dev）

**状态变更**：

- `APC-T011`：TODO → BLOCKED（notify payload parser + 0002 trigger migration static tests 完成；真实 LISTEN/NOTIFY worker 待验收）
- `APC-T012`：TODO → BLOCKED（sync contract validator + duplicate soft hint + PowerSync config skeleton 完成；真实 PowerSync 验收待执行）
- `APC-T019`：TODO → BLOCKED（Rules Admin validate/activate/audit dev API 完成；真实 EvidencePolicy DB/auth/audit 待验收）

**验证**：

```bash
make docs-check && make lint && make typecheck && make test && make rules-validate
# 125 passed, 1 warning; rule packs validated
```

---

## 第 20 轮 · 2026-07-09（APC-T013~T017 Normalization + State Engine dev chain）

**状态变更**：

- `APC-T013`：TODO → BLOCKED（parsers/service/in-memory derived store/tests 完成；DB 派生表写入待验收）
- `APC-T014`：TODO → BLOCKED（dedup/correction/scan_pending tests 完成；真实 event bus worker 待验收）
- `APC-T015`：TODO → BLOCKED（P0 projection pure functions/tests 完成；DB 集成待验收）
- `APC-T016`：TODO → BLOCKED（BabyStateEngine/snapshot repo/State API dev 完成；DB upsert 待验收）
- `APC-T017`：TODO → BLOCKED（dev event→normalization→state integration test 完成；真实 PG/PowerSync 链路待验收）

**验证**：

```bash
make docs-check && make lint && make typecheck && make test && make rules-validate
# 120 passed, 1 warning; rule packs validated
```

---

## 第 19 轮 · 2026-07-09（APC-T049/T050/T051/T052/T053 Android feature view models）

**目标**：继续开发不依赖 Android native toolchain 的 Android feature view models 与 flows。

**状态变更**：

- `APC-T049`：TODO → BLOCKED（Today view model/static tests 完成；前置与真实 UI 待验收）
- `APC-T050`：TODO → BLOCKED（Timeline view model/correction/delete/duplicate hint 完成；前置与真实 UI 待验收）
- `APC-T051`：TODO → BLOCKED（Alert Center view model/ack/feedback flow 完成；前置与真实 UI 待验收）
- `APC-T052`：TODO → BLOCKED（notification payload/channel/fullscreen/fallback/work manager static flow 完成；native integration 待验收）
- `APC-T053`：TODO → BLOCKED（Sleep Session view model/ROI save flow 完成；真实 UI/snapshot/ROI gesture 待验收）

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
make lint
make typecheck
make test
# 114 passed, 1 warning
```

---

## 第 18 轮 · 2026-07-09（APC-T045/T046/T047/T048 Android skeleton/static logic）

**目标**：继续开发不依赖 Android native toolchain 的 Android TS skeleton 与核心离线记录逻辑。

**状态变更**：

- `APC-T045`：TODO → BLOCKED（RN source skeleton/API client/theme/navigation/static tests 完成；Gradle/RN native build 待验收）
- `APC-T046`：TODO → BLOCKED（session/authService flow static tests 完成；secure storage/native integration 待验收）
- `APC-T047`：TODO → BLOCKED（sync schema/in-memory pending store static tests 完成；op-sqlite/PowerSync native integration 待验收）
- `APC-T048`：TODO → BLOCKED（Quick Record candidate/local event payload static tests 完成；UI/native offline write 待验收）

**完成内容**：

- Android-only React Native package/app skeleton。
- API client with base URL and Bearer token.
- Theme and route constants.
- Auth/session reducer and login/device registration API flow.
- LocalObservationEvent schema, in-memory pending store, PowerSync config skeleton.
- Quick Record candidate parser and local event payload builder.

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
make lint
make typecheck
make test
# 109 passed, 1 warning
```

---

## 第 17 轮 · 2026-07-09（APC-T054 DevOps + APC-T055 Fixtures + APC-T057 Fake Red Alert E2E + APC-T058 Security）

**目标**：继续开发不依赖真实设备/DB/Android 的 DevOps、fixtures、fake E2E 与安全回归能力。

**状态变更**：

- `APC-T054`：TODO → BLOCKED（run scripts/launchd/runbook 完成；真实 launchd/infra/Fregata 待验收）
- `APC-T055`：TODO → BLOCKED（fixtures/fakes/mock publisher 完成；真实 MQTT integration 待验收）
- `APC-T057`：TODO → BLOCKED（server fake red alert E2E 完成；Android notification E2E 待实现）
- `APC-T058`：TODO → BLOCKED（security regression suite 完成；真实 DB audit immutability 待验收）

**完成内容**：

- Dev run scripts、launchd server/fregata plist、deployment runbook。
- Reusable fake services and model response fixture。
- Mock mmWave publisher dry-run / optional aiomqtt publisher。
- Security tests for prompt injection dose, PII/canary/raw media, audit immutability static.
- Fake red alert delivery E2E over Notification/Escalation stack.

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
make lint
make typecheck
make test          # 104 passed, 1 warning
make security-test # 5 passed
make e2e-fake-test # 1 passed
make rules-validate
```

---

## 第 16 轮 · 2026-07-09（APC-T041 Firmware skeleton + APC-T044 Backup runbook/tasks）

**目标**：继续开发不依赖真实硬件/NAS 的固件与备份基础能力。

**状态变更**：

- `APC-T041`：TODO → BLOCKED（ESP32C6 PlatformIO skeleton/tests 完成；pio 编译与真实硬件待验收）
- `APC-T044`：TODO → BLOCKED（PG dump/media archive dry-run tasks/runbook/launchd/tests 完成；真实 pg_dump/NAS/restore drill 待验收）

**完成内容**：

- ESP32C6 firmware skeleton：PlatformIO、PubSubClient、config example、mock JSON payload publisher、README。
- Backup dry-run tasks：PG dump plan、media archive plan、launchd plist、Backup/Restore runbook、`make backup-dry-run`。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
make lint
make typecheck
make test
# 98 passed, 1 warning
make rules-validate
```

---

## 第 15 轮 · 2026-07-09（APC-T042 Media Storage + APC-T043 Export dev）

**目标**：继续开发不依赖真实 DB 的媒体加密存储、缩略图和导出基础。

**状态变更**：

- `APC-T042`：TODO → BLOCKED（AES-GCM file storage/thumbnail/dev API tests 完成；DB media_asset/audit/key management 待验收）
- `APC-T043`：TODO → BLOCKED（Markdown export/PDF placeholder/local file export tests 完成；真实 event/state query 与 audit/download auth 待集成）

**完成内容**：

- AES-GCM encrypted local media file store。
- In-memory MediaAssetRecord index 与 JSON/base64 dev upload/read API。
- Pillow thumbnail generation。
- Markdown summary renderer 与 PDF placeholder。
- ExportService 写入 runtime/exports local files。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 117 source files
make test
# 95 passed, 1 warning
make rules-validate
# rule packs validated
```

---

## 第 14 轮 · 2026-07-09（APC-T039 Camera Shadow + APC-T040 mmWave Parser/Mapper）

**目标**：继续开发不依赖真实 MQTT/DB/VLM 的 camera/mmWave shadow pipeline 基础。

**状态变更**：

- `APC-T039`：TODO → BLOCKED（Clip plan/FusionStateMachine/VLMDispatcher shadow tests 完成；真实 DB/VLM/媒体待验收）
- `APC-T040`：TODO → BLOCKED（frame parser/sensor mapper/topic whitelist subscriber tests 完成；真实 MQTT/DB 入库待验收）

**完成内容**：

- mmWave RadarFrame JSON/JSONL parser。
- SensorEventCandidate 与 ObservationEventCreate candidate mapper。
- MMWaveMQTTSubscriber skeleton：topic whitelist + handler 注入。
- Camera ClipRecorder plan：前 15s / 后 30s。
- FusionStateMachine：仅 active sleep session 分析；mmWave 单信号不产生红警；多信号输出 shadow candidate。
- VLMDispatcher：只通过注入 ModelGateway-compatible vision client，shadow mode 默认。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 109 source files
make test
# 90 passed, 1 warning
make rules-validate
# rule packs validated
```

---

## 第 13 轮 · 2026-07-09（uv-first 依赖修复 + APC-T037/T038 Camera/Sleep dev）

**目标**：按用户反馈将依赖安装改为 uv-first，并继续开发 Sleep Session / Camera mock 能力。

**状态变更**：

- `APC-T037`：TODO → BLOCKED（SleepSession state machine/dev API/ROI tests 完成；DB/audit 验收待 PostgreSQL）
- `APC-T038`：TODO → BLOCKED（devices.yaml/mock snapshot API/adapters placeholders/tests 完成；真实设备验收待后续）

**修复内容**：

- `ensure-dev-deps.py` 改为 uv-first：优先 `uv pip install --python <当前venv python> -e .[dev]`，仅 uv 不存在时 fallback 到 pip/ensurepip。

**开发内容**：

- Sleep Session state machine：active/paused/ended 与 analysis_allowed gate。
- ROI 配置与 sleep session dev API。
- Camera mock snapshot API：`GET /api/v1/cameras/{camera_id}/snapshot` 返回 PNG。
- ISAPI/Fregata 适配入口 placeholder 与 devices.yaml。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 102 source files
make test
# 83 passed, 1 warning
make rules-validate
# rule packs validated
```

---

## 第 12 轮 · 2026-07-09（pipless venv 修复 + APC-T034/T035/T036 dev 逻辑）

**目标**：修复用户重新验收发现的 pipless uv venv 问题，并继续开发 Alert escalation、Device Health 与 Scheduler dev 逻辑。

**状态变更**：

- `APC-T034`：TODO → BLOCKED（EscalationStateMachine/虚拟时钟 tests 完成；真实通道 cancel/审计待验收）
- `APC-T035`：TODO → BLOCKED（DeviceHealthMonitor/MockProbe/gray alert tests 完成；真实 probes 与 DB alert 持久化待验收）
- `APC-T036`：TODO → BLOCKED（manual SchedulerRunner/jobs tests 完成；真实 worker/DB/audit 待接入）

**修复内容**：

- `ensure_dev_deps.py` 支持当前 Python 无 pip 的 uv venv：先尝试 pip，再 ensurepip，最后 `uv pip install --python <sys.executable> -e .[dev]`。
- 保持 Makefile 自动依赖安装，避免 alembic/structlog/python-ulid/pytest-asyncio 缺失导致验收失败。

**开发内容**：

- `notification/escalation.py`：0s/60s/90s 升级状态机与 ack cancel。
- `health/monitor.py`：mock probes、gray alert 生成、device health snapshot。
- `scheduler/runner.py` 与 jobs：morning brief、vaccine due、supplement、health check。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 95 source files
make test
# 78 passed, 1 warning
make rules-validate
# rule packs validated
```

---

## 第 11 轮 · 2026-07-09（验收依赖修复 + APC-T031 Alert + APC-T032 Channels + APC-T033 Notification Orchestrator）

**目标**：修复用户集中验收暴露的本地依赖缺失问题，并继续开发不依赖真实 DB 的 Alert/Notification 纯逻辑。

**状态变更**：

- `APC-T031`：TODO → BLOCKED（Alert dev repo/API/MemoryAuditSink tests 完成；DB audit 集成待验收）
- `APC-T032`：TODO → BLOCKED（NotificationChannel/Fake channels/config/tests 完成；真实 FCM/TTS/Camera 待设备验收）
- `APC-T033`：TODO → BLOCKED（NotificationOrchestrator fan-out/in-memory delivery receipts/tests 完成；DB delivery repo 待验收）

**修复内容**：

- `server/scripts/ensure_dev_deps.py`：自动检查并安装当前 Python 环境缺失依赖。
- `Makefile`：`test/lint/typecheck/rules-validate/db-migrate/db-current/run-dev` 自动先执行 `ensure-dev-deps`。
- `pyproject.toml`：补充 setuptools package discovery，支持 `pip install -e .[dev]`。

**开发内容**：

- `InMemoryAlertRepository` 与 Alert API dev routes。
- NotificationChannel Protocol、DeliveryReceipt 与 Fake channels。
- NotificationOrchestrator fan-out，red/orange 多通道，FCM 失败不阻断 fallback。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 87 source files
make test
# 72 passed, 1 warning
make rules-validate
# rule packs validated

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

---

## 第 10 轮 · 2026-07-09（APC-T030 P0 Copilot wrappers）

**目标**：继续并行开发不依赖真实 DB 的 P0 Copilot 外壳与 Rule Engine 调用链。

**状态变更**：

- `APC-T030`：TODO → BLOCKED（P0 Copilot wrappers/tests 完成；前置 T020/T022/T023/T028/T029 未 DONE，DB/Memory/audit 集成待验收）

**完成内容**：

- `ProactiveCopilot`：生成 reminder candidates，不自行生成 alert level。
- `FamilyMemoryCopilot`：生成 memory_update candidate，requires_confirmation=true。
- `VaccinePlannerCopilot`：调用 VaccineRuleModule，输出 rule_result/evidence。
- `GrowthMilestoneCopilot`：调用 GrowthRuleModule，输出 percentile/evidence。
- `MedicationSafetyCopilot`：调用 MedicationRuleModule，结构化 dose 只来自 Rule Engine。
- Orchestrator 默认 registry 注册 P0 Copilots，可通过显式 intent 选择。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 80 source files
make test
# 67 passed, 1 warning
make rules-validate
# rule packs validated

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

---

## 第 9 轮 · 2026-07-09（APC-T026 Memory + APC-T027 Logger Copilot + APC-T028 Orchestrator + APC-T029 Dose Interceptor）

**目标**：继续并行开发不依赖真实 DB 的 Copilot/Orchestrator 安全链路。

**状态变更**：

- `APC-T026`：TODO → BLOCKED（M1-M5 snapshot/in-memory MemoryStore 完成；前置 T016 与 Local RAG 真实适配未完成）
- `APC-T027`：TODO → BLOCKED（Copilot base/registry/logger parser/tests 完成；前置 T026 未 DONE）
- `APC-T028`：TODO → BLOCKED（IntentRouter/ContextBuilder/OutputGuard/Orchestrator dev API 完成；T027/T006 未 DONE）
- `APC-T029`：TODO → BLOCKED（DoseInterceptor 纯逻辑/安全测试完成；T028 与真实 audit_log 写入未 DONE）

**完成内容**：

1. **APC-T026 Memory snapshot**：MemorySnapshot、in-memory M1-M5 MemoryStore。
2. **APC-T027 Logger Copilot**：DomainCopilot 协议、CopilotRegistry、LoggerCopilot，支持中文记录候选。
3. **APC-T028 Orchestrator dev**：IntentRouter、ContextBuilder、OutputGuard、Orchestrator、`POST /api/v1/copilot/query`。
4. **APC-T029 Dose Interceptor**：拦截 mg/ml/毫升/滴/片，Rule Engine source 可通过，MemoryAuditSink 记录。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 75 source files
make test
# 62 passed, 1 warning
make rules-validate
# rule packs validated

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

---

## 第 8 轮 · 2026-07-09（APC-T022 Vaccine Planner + APC-T023 Growth Rules）

**目标**：继续并行开发不依赖真实 DB 的规则域，补齐 P0 Vaccine/Growth 纯逻辑。

**状态变更**：

- `APC-T022`：TODO → BLOCKED（VaccineRuleModule/规则包/golden tests 完成；前置 T018 与生产规则审查未完成）
- `APC-T023`：TODO → BLOCKED（GrowthRuleModule/简化 WHO fixture/golden tests 完成；前置 T018 与完整 WHO 表验收未完成）

**完成内容**：

1. **APC-T022 Vaccine Planner**：
   - `server/app/rule_engine/domains/vaccine.py`：按 birth_date/as_of/records 输出 due_date/status/evidence。
   - `config/rules/vaccine/cn-nip-2024.yaml`：CN NIP dev fixture。
   - Golden cases 覆盖出生当天计划、逾期、completed/skipped 状态。

2. **APC-T023 Growth Rules**：
   - `server/app/rule_engine/domains/growth.py`：按 sex/age_months/metric/value 返回 percentile_band/evidence。
   - `config/rules/growth/who-0-5.yaml`：简化 WHO-compatible fixture。
   - Golden cases 覆盖男/女、不同月龄、边界百分位；单点不强告警。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 62 source files
make test
# 53 passed, 1 warning
make rules-validate
# growth / medication / triage / vaccine packs validated and hashed

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

---

## 第 7 轮 · 2026-07-09（APC-T018 Rule Engine + APC-T020 Medication + APC-T021 Triage/Threshold）

**目标**：继续并行开发不依赖真实 DB 的规则引擎纯逻辑，为后续 Medication/Triage/Vaccine/Growth 与 Copilot 链路打基础。

**状态变更**：

- `APC-T018`：TODO → BLOCKED（kernel/loader/registry/in-memory EvidencePolicy repo/rules-validate 完成；DB persistence/audit 待 PostgreSQL）
- `APC-T020`：TODO → BLOCKED（MedicationRuleModule/规则包/golden tests 完成；前置 T018 未 DONE）
- `APC-T021`：TODO → BLOCKED（Triage/Threshold pure rules/golden tests 完成；前置 T018/T016 未 DONE）

**完成内容**：

1. **APC-T018 Rule Engine Kernel**：
   - RuleInput / RuleResult / EvidenceItem / Verdict。
   - YAML RulePack loader、hash、schema validation。
   - RuleRegistry、RuleEngine façade。
   - InMemoryEvidencePolicyRepository。
   - `make rules-validate`。

2. **APC-T020 Medication Rules**：
   - MedicationRuleModule。
   - `config/rules/medication/base.yaml`。
   - Golden cases 覆盖 allow/block、未知体重、未知浓度、布洛芬月龄禁忌、剂量计算。

3. **APC-T021 Triage / Threshold Rules**：
   - 3 月龄以下 ≥38°C 红色分诊。
   - danger signals orange/red candidate。
   - 趋势告警双条件。
   - mmWave 单信号禁止红警。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 60 source files
make test
# 49 passed, 1 warning
make rules-validate
# medication / triage packs validated and hashed

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

---

## 第 6 轮 · 2026-07-09（APC-T009 ObservationEvent + APC-T010 Events API dev）

**目标**：继续并行开发不依赖真实 DB 的 MVP 服务端记录链路代码。

**状态变更**：

- `APC-T009`：TODO → BLOCKED（Pydantic 契约、idempotency、in-memory repo/unit tests 完成；DB repository/upsert 集成验收待 PostgreSQL）
- `APC-T010`：TODO → BLOCKED（dev/in-memory API 与 MemoryAuditSink 测试完成；真实 DB/audit_log 集成验收待 PostgreSQL）

**完成内容**：

1. **APC-T009 ObservationEvent 契约 / Repository**：
   - `server/app/events/domain/observation_event.py`：统一事件契约与 timezone-aware 校验。
   - `server/app/events/service/idempotency.py`：event_id 幂等冲突校验。
   - `server/app/events/infra/repository.py`：EventRepository Protocol 与 InMemoryEventRepository。

2. **APC-T010 Events API dev**：
   - `server/app/events/api/routes.py`：创建、查询、纠错、软删除 API。
   - `server/app/main.py`：注册 events router，注入 InMemoryEventRepository 与 MemoryAuditSink。
   - 测试覆盖 create/list/correct/delete 与审计记录。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 49 source files
make test
# 42 passed, 1 warning

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

**阻塞说明**：

真实 PostgreSQL repository、PowerSync 写入契约与 audit_log 持久化仍需 Docker/PostgreSQL 环境验收，因此 `APC-T009`、`APC-T010` 保持 `BLOCKED`。

---

## 第 5 轮 · 2026-07-09（APC-T007 Auth/RBAC 代码 + APC-T008 Auth API dev 代码）

**目标**：按用户指示继续并行开发不依赖真实 DB 的代码，严格不将依赖 PostgreSQL 集成验收的任务标记 DONE。

**状态变更**：

- `APC-T007`：TODO → BLOCKED（domain/service/JWT/RBAC/in-memory repo/unit tests 完成；DB repo 与真实审计验收待 PostgreSQL）
- `APC-T008`：TODO → BLOCKED（dev/in-memory Auth API 与 seed 脚本完成；DB 持久化与 audit_log 集成验收待 PostgreSQL）

**完成内容**：

1. **APC-T007 Auth/RBAC**：
   - `server/app/auth/domain/models.py`：Role、DeviceKind、Family、User、Device、Principal。
   - `server/app/auth/service/passwords.py`：PBKDF2-HMAC-SHA256 hash/verify，明文不存储。
   - `server/app/auth/service/jwt_service.py`：本地 HS256 JWT，claims 包含 user_id/family_id/role/device_id。
   - `server/app/auth/service/auth_service.py`：family/admin 创建、登录、token Principal、RBAC、设备注册。
   - `server/app/auth/infra/repository.py`：AuthRepository Protocol 与 InMemoryAuthRepository。

2. **APC-T008 Auth API / seed dev**：
   - `server/app/auth/api/routes.py`：`/api/v1/auth/init-family`、`/login`、`/refresh`、`/me`、`/devices/register`。
   - `server/scripts/seed_family.py`：dev/in-memory seed 脚本，可在无 DB 环境运行。
   - `server/app/main.py`：注册 auth router，并在 dev/mock 模式注入 InMemoryAuthRepository AuthService。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 40 source files
make test
# 36 passed, 1 warning
python3 server/scripts/seed_family.py
# outputs in-memory family_id/admin_user_id/access_token JSON

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

**阻塞说明**：

当前实现已支持 dev/in-memory flow，但还未接入 PostgreSQL Auth repository、真实 seed DB 写入与 mutating audit_log 集成验收。因此 `APC-T007`、`APC-T008` 均保持 `BLOCKED`。

---

## 第 4 轮 · 2026-07-09（APC-T004 Schema 代码 + APC-T006 Audit 代码）

**目标**：继续推进 DB 相关任务的代码实现，但严格按 DoD 处理无法在当前沙盒完成的 PostgreSQL 集成验收。

**状态变更**：

- `APC-T004`：TODO → BLOCKED（metadata/migration/static/offline SQL 完成；等待 PostgreSQL 空库 upgrade/downgrade 验收）
- `APC-T006`：TODO → BLOCKED（service/decorator/unit tests 完成；等待 audit_log DB insert/update/delete 集成验收）

**完成内容**：

1. **APC-T004 Schema 初版**：
   - `server/app/models.py`：SQLAlchemy metadata，覆盖架构与工程设计要求的核心表。
   - `server/migrations/versions/0001_initial_schema.py`：Alembic 初版 migration。
   - migration 包含：updated_at trigger、audit_log append-only trigger、`REVOKE UPDATE, DELETE ON TABLE audit_log FROM app_user` 条件执行。
   - schema 测试覆盖 required tables、ObservationEvent PK/状态字段/索引、audit immutability SQL。
   - Alembic offline SQL：`python3 -m alembic -c alembic.ini upgrade head --sql` 通过。

2. **APC-T006 Audit 代码**：
   - `server/app/observability/audit.py`：AuditActor、AuditRecord、AuditService、MemoryAuditSink、AuditWriteError。
   - `server/app/common/audit_decorator.py`：`@audit` 装饰器。
   - 单元测试覆盖 before/after 捕获与高风险操作无审计 sink 时阻断。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 29 source files
make test
# 30 passed, 1 warning
python3 -m alembic -c alembic.ini upgrade head --sql
# offline SQL generation passed

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

**阻塞说明**：

当前沙盒无 Docker/PostgreSQL，无法完成 `APC-T004` 的空库 `alembic upgrade head`、迁移升降级集成测试，也无法完成 `APC-T006` 的 audit_log DB 插入与 UPDATE/DELETE 被拒绝验证。因此二者均保持 `BLOCKED`，未标记 DONE。

---

## 第 3 轮 · 2026-07-08（APC-T003 基础设施代码 / APC-T024 Model Gateway / APC-T025 Privacy Adapter）

**目标**：继续尽可能多推进任务；严格遵守架构边界与 DoD。

**状态变更**：

- `APC-T003`：TODO → BLOCKED（代码/配置/静态验证完成；Docker 容器健康验收受环境阻塞）
- `APC-T024`：TODO → DONE
- `APC-T025`：TODO → DONE

**完成内容**：

1. **APC-T003 代码与配置**：
   - `deploy/docker-compose.yml`：PostgreSQL 15、Mosquitto 2、PowerSync official service。
   - PowerSync 使用 `journeyapps/powersync-service:latest`；为避免引入架构外 MongoDB，bucket storage 配置为 PostgreSQL。
   - `server/app/db.py`：SQLAlchemy async engine/session primitives。
   - `alembic.ini`、`server/migrations/env.py`：Alembic 初始化。
   - Makefile 增加 `infra-up`、`infra-down`、`infra-logs`、`db-migrate`、`db-current`。
   - 测试覆盖 compose/service.yaml 配置、Postgres URL normalize、Alembic offline SQL generation。

2. **APC-T024 Model Gateway**：
   - 新增 `server/app/model_gateway/`。
   - 支持 Smart Proxy `/v1/messages`、chat、vision、routing plan、FakeModelClient。
   - 新增 `config/routing_plans.yaml` 与 `config/models.yaml`。
   - 测试使用 httpx MockTransport，CI 不调用真实模型。

3. **APC-T025 Privacy Adapter**：
   - 新增 `server/app/privacy/adapter.py`，通过适配层复用工厂 `_infra.network.privacy_gateway`。
   - 文本云出站前执行 PII 脱敏与 canary 检查。
   - 原始媒体云出站显式阻断。
   - 测试覆盖 PII 脱敏、canary 阻断、媒体出站阻断。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 26 source files
make test
# 25 passed, 1 warning

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

**阻塞说明**：

当前沙盒无 Docker CLI，无法执行 `make infra-up` 容器健康验收，因此 `APC-T003` 不满足完整 DoD，状态保持 `BLOCKED`，没有标记 DONE。

---

## 第 2 轮 · 2026-07-08（APC-T002 FastAPI 应用壳 + APC-T005 可观测性基础）

**目标**：在不改变架构边界的前提下，完成 `APC-T002`；由于 `APC-T005` 仅依赖 `APC-T002`，同步完成可观测性基础。`APC-T003` 需要 Docker 容器健康验收，当前沙盒无 Docker CLI，因此未标记 DONE。

**状态变更**：

- `APC-T002`：TODO → IN_PROGRESS → DONE
- `APC-T005`：TODO → IN_PROGRESS → DONE
- `APC-T003`：保持 TODO，作为下一顺序任务

**完成内容**：

1. **FastAPI 应用壳（APC-T002）**：
   - `server/app/main.py`：`create_app()`、全局 `app`、lifespan、health router、metrics endpoint。
   - `server/app/settings.py`：`pydantic-settings`，支持 `PARENTING_` 与 `__` 嵌套。
   - `server/app/di.py`：AppContainer、WorkerRegistry，预留 worker 生命周期接口。
   - `server/app/common/`：ULID、timezone-aware clock、AppError/ErrorResponse、Repository Protocol、InMemoryEventBus。
   - `server/app/gateway/exception_handlers.py`：统一错误格式 `{code,message,evidence,trace_id}`。

2. **可观测性基础（APC-T005）**：
   - `server/app/observability/logger.py`：structlog JSON 日志、敏感字段与 PII mask。
   - `server/app/observability/metrics.py`：Prometheus metrics registry 与 `/metrics`。
   - `server/app/observability/tracing.py`：OpenTelemetry SDK provider，未配置 exporter 时安全降级。
   - `server/app/gateway/middleware/logging.py`：request_id/trace_id 注入、结构化请求日志、HTTP 指标记录。
   - `server/app/health/api.py`：`/healthz` 与 `/api/v1/system/health`。

3. **测试补充**：
   - `tests/test_settings_ids_errors.py`：settings env override、ULID、timezone-aware clock、异常映射。
   - `tests/test_app_health_observability.py`：health/openapi、metrics、请求日志 request_id、PII mask。

**架构影响**：

- 无架构变更。
- 无新增基础设施。
- 未实现业务 worker、Auth、Event Store、DB 连接或同步逻辑。
- LLM / Rule Engine / Privacy Gateway / Notification Orchestrator 边界未改变。

**验证**：

```bash
cd projects/AI-Parenting-Copilot
make docs-check
# Project docs-check passed.
make lint
# All checks passed.
make typecheck
# Success: no issues found in 20 source files
make test
# 11 passed, 1 warning
python3 -m uvicorn server.app.main:app --host 127.0.0.1 --port 8765
# /healthz smoke: HTTP 200

cd ../..
make docs-check
# Blockers: 0; Warnings: 1（architecture-sensitive terms review warning, non-blocking）
```

**风险 / 备注**：

- `APC-T003` 需要 Docker；当前沙盒 `docker` 命令不存在，因此后续若实现 T003，容器健康验收需要用户 Mac 或可用 Docker 环境配合。
- FastAPI TestClient 在当前依赖组合下输出 `StarletteDeprecationWarning`，不影响测试结果。

---

## 第 1 轮 · 2026-07-08（APC-T001 项目骨架初始化）

**目标**：严格依据 `docs/TASK_BACKLOG.md` 执行首个任务 `APC-T001`，只创建项目骨架和维护文档，不实现业务功能。

**状态变更**：

- `APC-T001`：TODO → IN_PROGRESS → DONE
- `APC-T002`：保持 TODO，作为下一最高优先级任务

**完成内容**：

1. 创建项目根工程元数据：
   - `README.md`
   - `Makefile`
   - `pyproject.toml`
   - `.env.example`
   - `.gitignore`

2. 创建项目级维护文档：
   - `docs/PROJECT_STATE.md`
   - `docs/DEV_LOG.md`
   - `docs/CHANGELOG.md`
   - `docs/HANDOFF.md`
   - `docs/ADR/ADR-001-project-bootstrap.md`

3. 创建项目骨架目录：
   - `server/app/__init__.py`
   - `android/.gitkeep`
   - `firmware/esp32c6/.gitkeep`
   - `config/.gitkeep`
   - `deploy/.gitkeep`
   - `runtime/.gitkeep`
   - `tests/test_project_structure.py`

4. 按用户最新指令完成清理与文档一致性修正：
   - 删除 `docs/~$TASK_BACKLOG家庭私有化 AI 育儿副驾驶系统-gpt-5.5-high.docx`。
   - 将项目文档内目录名统一为 `projects/AI-Parenting-Copilot/`。
   - 明确工厂能力背景使用工厂根目录 `PROJECT_DOSSIER_V5.md`，项目内旧拷贝不作为执行 SSOT。

**架构影响**：

- 无架构变更。
- 无技术路线变更。
- 无模块职责变更。
- 无新增基础设施。
- 本轮仅落地 `APC-T001` 要求的工程骨架。

**验证**：

```bash
make docs-check
make lint
make typecheck
make test
```

**风险 / 备注**：

- `APC-T001` 阶段尚未实现 FastAPI，因此 `make run-dev` 仅输出明确提示。
- 如果本地未安装 `ruff` / `mypy`，Makefile 会提示跳过正式 ruff/mypy 检查；后续任务引入开发依赖后应执行完整静态检查。

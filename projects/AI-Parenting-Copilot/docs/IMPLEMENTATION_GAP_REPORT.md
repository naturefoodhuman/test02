<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-08-05 02:35:00
-->

# IMPLEMENTATION_GAP_REPORT —— 实现缺口报告

## 当前总览

```text
总任务：59
DONE：49
BLOCKED：10
TODO / IN_PROGRESS：0
```

结论：代码实现、dry-run、contract report、fake E2E、preflight 和 closeout tooling 已基本完成；剩余 10 项是外部验证项。

## 代码已完成的主要能力

- DB-backed API runtime / worker / normalization / state。
- PowerSync contract / heartbeat / probes。
- Android native fallback：Auth、Quick Record、Today、Timeline、Alert Center、Sleep Session、Rule Evaluation、Critical Alert。
- Rule Engine：medication、triage、thresholds、vaccine fixture、growth fixture。
- P0 Copilots：record candidate、family memory、vaccine/growth/medication wrappers。
- Notification Orchestrator、多通道 fake/dev delivery、escalation report。
- Camera/mmWave shadow：API、repository、fusion、VLM/Fregata/ISAPI adapters、fixture replay。
- Media / Export / Backup dry-run / manifest verifier。
- DevOps：launchd validator、deployment readiness、P0 readiness。
- Security regression：dose / prompt injection / privacy / audit immutability。

## 剩余缺口表

| APC | 剩余内容 | 类型 | 当前自动化支持 |
|---|---|---|---|
| T022 | CN vaccine production signoff | 人审 | rule review packet, signoff validator |
| T023 | WHO full LMS growth review | 人审/数据 | rule review packet, signoff validator |
| T030 | P0 Copilot production closeout | 依赖 T022/T023 | closeout gate, evidence template |
| T036 | Scheduler production/long-running | 人审+长期运行 | scheduler API, alert bridge, evidence template |
| T038 | Camera RTSP/ISAPI device | 真设备 | ISAPI adapter, camera API, evidence template |
| T039 | Camera/Fregata/VLM shadow | 真设备/VLM | Fregata bridge, shadow APIs, shadow-test |
| T040 | mmWave MQTT device soak | 真硬件/MQTT | replay report, MQTT worker, evidence template |
| T041 | ESP32C6 pio compile/flash | 真硬件/toolchain | firmware-preflight, evidence template |
| T044 | Real pg_dump/NAS restore drill | NAS/DB | backup verifier, restore dry-run, evidence template |
| T059 | 7-night shadow/soak | 长稳态 | p0-readiness, soak/locustfile, evidence template |

## 推荐执行顺序

1. `make external-validation-bundle` 生成全部证据模板。
2. 先完成可快速执行的本地类：T044 restore drill、T041 pio build、T040 MQTT smoke。
3. 再做设备类：T038 camera、T039 Fregata/VLM shadow。
4. 并行发起人审：T022/T023。
5. 人审完成后关闭 T030/T036。
6. 最后执行 T059 7-night shadow/soak。

## 关闭机制

外部证据完成后执行：

```bash
make apc-closeout-gate
make apc-closeout-recommendations
make apc-backlog-patch-plan
```

只有 `apc-closeout-gate` 显示某项 `ready_to_close` 后，才建议将对应任务改为 DONE。

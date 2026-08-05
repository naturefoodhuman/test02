<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-08-05 02:35:00
-->

# ARCHITECTURE_COMPLIANCE_AUDIT —— 架构一致性核查

## 结论

**状态**：`pass_with_external_blockers`

本轮对照 `docs/ARCHITECTURE_FINAL.md`、`docs/ENGINEERING_DESIGN.md`、`docs/TASK_BACKLOG.md` 与代码实现做静态核查。核心架构边界未发现破坏；剩余风险集中在外部人审/真设备/NAS/长稳态，不是本地代码路径缺失。

可复现命令：

```bash
make architecture-audit
```

输出：

```text
runtime/reports/architecture-compliance-audit.json
runtime/reports/architecture-compliance-audit.md
```

## 架构铁律核查

| 规则 | 核查结果 | 证据 |
|---|---:|---|
| LLM 只能经 Model Gateway | PASS | `server/app/model_gateway/client.py`, `server/app/model_gateway/routing.py` |
| 云出站隐私边界 | PASS | `server/app/privacy/adapter.py`, `tests/test_privacy_adapter.py` |
| 剂量/阈值/医疗判断只能由 Rule Engine 输出 | PASS | `server/app/rule_engine/api/routes.py`, P0 rule domains |
| LLM/Copilot 剂量文本必须被拦截 | PASS | `server/app/orchestrator/dose_interceptor.py`, security tests |
| Alert delivery 只能走 Notification Orchestrator | PASS | `server/app/notification/orchestrator.py`, alert API, red alert E2E substitute |
| mutating API route module 必须接审计 | PASS | `server/app/**/api/routes.py` 静态扫描均包含 `record_request_audit` |
| Android 离线记录不丢 | PASS | native `insertPending`, pending drain 2xx 后 `markSynced`, ack failure requeue |
| DB-backed runtime smoke 存在 | PASS | `api-db-smoke-test`, `worker-db-smoke-test`, `powersync-smoke-test` |
| closeout / external evidence 控制存在 | PASS | readiness、external evidence、closeout gate、patch plan |
| Backlog 状态一致 | PASS | 当前 `49 DONE / 10 BLOCKED` |

## 自动化核查项

新增自动化模块：

```text
server/app/ops/architecture_compliance.py
server/scripts/architecture_compliance_audit.py
```

测试：

```text
tests/test_architecture_compliance.py
```

## 当前剩余外部 blocker

- `APC-T022`：CN vaccine production signoff。
- `APC-T023`：full WHO growth LMS table / reviewer signoff。
- `APC-T030`：P0 Copilot closeout，依赖 T022/T023。
- `APC-T036`：Scheduler production / long-running validation。
- `APC-T038`：real camera RTSP/ISAPI validation。
- `APC-T039`：real Camera/Fregata/VLM shadow validation。
- `APC-T040`：real mmWave MQTT device soak。
- `APC-T041`：ESP32C6 PlatformIO compile/flash。
- `APC-T044`：real pg_dump/NAS/restore drill。
- `APC-T059`：seven-night shadow/soak。

## 判断

代码层面已进入外部验收阶段；不建议把上述外部 blocker 伪造为 DONE。后续应按：

```bash
make external-validation-bundle
make apc-closeout-gate
make apc-closeout-recommendations
make apc-backlog-patch-plan
```

来收集证据并生成可审核关闭建议。

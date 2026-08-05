<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-08-05 02:35:00
-->

# RELEASE_READINESS_REPORT —— P0 发布准备状态

## 自动化 readiness 结论

当前自动化状态：

```text
ready_for_external_validation
```

可复现：

```bash
make p0-readiness
```

## 当前不可省略的外部验收

- Vaccine/Growth 人审不能省略。
- 真实 Android/PowerSync/FCM 设备链路不能由 fake E2E 替代。
- 真实 RTSP/ISAPI/Fregata/mmWave/ESP32C6/NAS 不能由 mock 替代。
- 7 晚 shadow/soak 不能由单次 shadow-test 替代。

## 安装部署建议

### 本地服务端

```bash
cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory/projects/AI-Parenting-Copilot
export PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting"
export PARENTING_POWERSYNC__URL="http://127.0.0.1:9081"
make infra-up
make db-migrate
make db-current
make api-db-smoke-test
make worker-db-smoke-test
make powersync-smoke-test
make run-api
```

### 独立健康检查终端

```bash
make api-health-smoke
make p0-readiness
make external-validation-bundle
```

### Android

```bash
cd android/android
./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

真机使用 Mac 局域网 API URL，例如：

```text
http://<mac-lan-ip>:8000
```

### 外部验收证据

```bash
make external-validation-bundle
```

然后按 bundle 中的 `external-evidence/*.json` 与 `rule-signoffs/*.json` 填证据。

## 上线前 gate

```bash
make architecture-audit
make p0-readiness
make external-validation-plan
make apc-closeout-gate
make apc-closeout-recommendations
make apc-backlog-patch-plan
make security-test
make e2e-fake-test
make docs-check
```

## 结论

项目可以进入本地外部验收和试运行准备，但不应宣称 production ready，直到 10 个外部 blocker 有证据并通过 closeout gate。

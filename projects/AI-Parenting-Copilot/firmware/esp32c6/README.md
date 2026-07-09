<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-07-09 09:20:00
-->


# ESP32C6 mmWave MQTT Firmware Skeleton

Target board: Seeed Studio XIAO ESP32C6.

## Configure

```bash
cp config.h.example src/config.h
# edit WiFi/MQTT values locally; do not commit src/config.h
```

## Build

```bash
cd firmware/esp32c6
pio run
```

## Payload

The skeleton publishes JSON to `baby/radar/telemetry` with fields:

- `presence`
- `state`
- `breathing_rate`
- `heart_rate`
- `abnormal_event`
- `timestamp`

The current parser is a mock/simple payload generator until the final MR60BHA2 serial
frame protocol is confirmed.

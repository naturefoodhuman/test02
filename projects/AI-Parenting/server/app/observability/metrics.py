# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
#
# app/observability/metrics.py —— Prometheus 指标定义。
# 依据：ENGINEERING_DESIGN §10.2（Metrics，对应 PRD §20）；ARCHITECTURE_FINAL §22.3；TASK_BACKLOG APC-T005。
# 设计：prometheus_client 定义 §10.2 列出的核心指标（Counter/Histogram/Gauge）。
#       /metrics 端点在 health/api.py 暴露（prometheus_client.make_asgi_app 或 generate_latest）。
#       指标名严格对齐 §10.2，label 维度按文档。

"""Prometheus 指标定义（ENGINEERING_DESIGN §10.2）。

指标清单（§10.2）：
    parenting_record_latency_seconds（Histogram）— 记录写入延迟。
    voice_normalization_success_ratio（Gauge）— 语音归一化成功率。
    sync_lag_seconds（Gauge）— 同步延迟。
    offline_backfill_success_total / offline_backfill_failed_total（Counter）— 离线补传成功/失败。
    alert_delivery_total{level,channel,status}（Counter）— 告警送达。
    red_alert_delivery_seconds（Histogram）— 红色告警送达延迟。
    rule_engine_evaluations_total{domain,verdict}（Counter）— 规则引擎评估。
    dose_intercept_total{trigger}（Counter）— 剂量拦截。
    device_online{device}（Gauge）— 设备在线。
    llm_calls_total{plan,route,status}（Counter）— LLM 调用。
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, generate_latest

# ---- 记录写入延迟 ----
record_latency_seconds = Histogram(
    "parenting_record_latency_seconds",
    "ObservationEvent 记录写入延迟（秒）",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# ---- 语音归一化成功率 ----
voice_normalization_success_ratio = Gauge(
    "voice_normalization_success_ratio",
    "语音归一化成功率（0-1）",
)

# ---- 同步延迟 ----
sync_lag_seconds = Gauge(
    "sync_lag_seconds",
    "PowerSync 同步延迟（秒）",
)

# ---- 离线补传 ----
offline_backfill_success_total = Counter(
    "offline_backfill_success_total",
    "离线补传成功总数",
)
offline_backfill_failed_total = Counter(
    "offline_backfill_failed_total",
    "离线补传失败总数",
)

# ---- 告警送达 ----
alert_delivery_total = Counter(
    "alert_delivery_total",
    "告警送达总数",
    labelnames=("level", "channel", "status"),
)
red_alert_delivery_seconds = Histogram(
    "red_alert_delivery_seconds",
    "红色告警送达延迟（秒）",
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

# ---- 规则引擎 ----
rule_engine_evaluations_total = Counter(
    "rule_engine_evaluations_total",
    "规则引擎评估总数",
    labelnames=("domain", "verdict"),
)
dose_intercept_total = Counter(
    "dose_intercept_total",
    "剂量拦截总数",
    labelnames=("trigger",),
)

# ---- 设备在线 ----
device_online = Gauge(
    "device_online",
    "设备在线状态（1=在线, 0=离线）",
    labelnames=("device",),
)

# ---- LLM 调用 ----
llm_calls_total = Counter(
    "llm_calls_total",
    "LLM 调用总数",
    labelnames=("plan", "route", "status"),
)


def metrics_response_body() -> bytes:
    """生成 Prometheus exposition 格式响应体（供 /metrics 端点）。"""
    return generate_latest()


__all__ = [
    "alert_delivery_total",
    "device_online",
    "dose_intercept_total",
    "llm_calls_total",
    "metrics_response_body",
    "offline_backfill_failed_total",
    "offline_backfill_success_total",
    "record_latency_seconds",
    "red_alert_delivery_seconds",
    "rule_engine_evaluations_total",
    "sync_lag_seconds",
    "voice_normalization_success_ratio",
]

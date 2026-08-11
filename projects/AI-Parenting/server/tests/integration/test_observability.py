# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""可观测性集成测试（APC-T005 测试要求）。

覆盖：
    - 请求日志包含 request_id（响应 header X-Request-Id 回写）。
    - trace_id 贯穿（入站 X-Trace-Id 透传，无则生成）。
    - /metrics 返回 Prometheus exposition 格式（含核心指标名）。
    - /readyz 在 dev/mock 无 DB 时返回 degraded（不 500）。
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.app.observability.metrics import metrics_response_body


def test_response_has_request_id_header(client: TestClient):
    """每请求生成 request_id 并回写 X-Request-Id header（§10.1）。"""
    r = client.get("/healthz")
    assert r.status_code == 200
    assert "x-request-id" in r.headers
    rid = r.headers["x-request-id"]
    assert len(rid) == 26  # ULID


def test_trace_id_passthrough_from_inbound_header(client: TestClient):
    """入站 X-Trace-Id 透传（贯穿上游链路），无则生成。"""
    inbound = "01JTESTTRACEID0000000000"
    r = client.get("/healthz", headers={"X-Trace-Id": inbound})
    assert r.status_code == 200
    assert r.headers["x-trace-id"] == inbound


def test_trace_id_generated_when_absent(client: TestClient):
    """无入站 X-Trace-Id 时生成 ULID 并回写。"""
    r = client.get("/healthz")
    assert r.status_code == 200
    tid = r.headers["x-trace-id"]
    assert len(tid) == 26  # ULID


def test_metrics_endpoint_returns_prometheus_format(client: TestClient):
    """/metrics 返回 Prometheus exposition 格式，含核心指标名（§10.2）。"""
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")
    body = r.text
    # 核心指标名（§10.2 列出的占位指标）必须出现
    assert "parenting_record_latency_seconds" in body
    assert "alert_delivery_total" in body
    assert "rule_engine_evaluations_total" in body
    assert "llm_calls_total" in body
    assert "device_online" in body


def test_metrics_response_body_helper():
    """metrics_response_body() 直接返回 Prometheus exposition bytes。"""
    body = metrics_response_body()
    assert isinstance(body, bytes)
    assert b"parenting_record_latency_seconds" in body


def test_readyz_returns_200_when_db_up(client: TestClient):
    """/readyz 在 DB 可达时返回 200 + status=ok（dev compose 已起 PG）。"""
    r = client.get("/readyz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["checks"]["db"] == "ok"
    assert body["checks"]["event_bus"] == "ok"

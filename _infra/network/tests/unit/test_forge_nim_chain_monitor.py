# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-12 10:20:00

"""Tests for FORGE NIM chain monitor classification."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.diagnostics.forge_nim_chain_monitor import (  # noqa: E402
    ChainSnapshot,
    classify_snapshot,
    count_patterns,
    summarize_samples,
)


def _snapshot(smart: dict, nim: dict) -> ChainSnapshot:
    return ChainSnapshot(
        local_time="2026-08-12 10:00:00 +0800",
        epoch=1.0,
        smart_health={"status": "ok"},
        nim_health={"status": "ok"},
        smart_status=smart,
        nim_stats=nim,
    )


def test_count_patterns_detects_common_errors() -> None:
    counts = count_patterns(
        'HTTP 429 Too Many Requests\nReadTimeout\nNo NVIDIA NIM key available\naddress already in use\n'
    )

    assert counts["http_429"] >= 1
    assert counts["read_timeout"] == 1
    assert counts["no_key_available"] == 1
    assert counts["bind_in_use"] == 1


def test_classify_detects_upstream_cooldown_and_long_attempts() -> None:
    smart = {
        "active_requests": 0,
        "total_requests": 343,
        "total_errors": 296,
        "retry": {"retry_counters": {"429": 269}},
        "circuit_breaker": {"state": "closed"},
        "context_budget": {
            "soft_tokens": 162201,
            "max_tokens": 902752,
            "last": {"est_before": 85322, "est_after": 85322},
        },
    }
    nim = {
        "request_count": 343,
        "retry_count": 58,
        "settings": {
            "max_attempts_per_request": 2,
            "read_timeout_seconds": 1200.0,
            "request_wall_timeout_seconds": 1500.0,
            "enable_fallback": False,
        },
        "pool": {
            "keys": [
                {"key_id": "key-1", "in_cooldown": True, "available_in_seconds": 93.0, "consecutive_429": 4},
                {"key_id": "key-2", "in_cooldown": False, "consecutive_429": 1},
            ]
        },
    }

    findings = classify_snapshot(_snapshot(smart, nim))
    codes = {item.code for item in findings}

    assert "NVIDIA_UPSTREAM_429_COOLDOWN" in codes
    assert "SMART_SEES_429_FROM_NIM" in codes
    assert "LONG_TIMEOUT_WITH_MULTIPLE_ATTEMPTS" in codes


def test_classify_detects_busy_keys() -> None:
    smart = {"active_requests": 1, "total_requests": 13, "total_errors": 12, "retry": {"retry_counters": {}}, "circuit_breaker": {"state": "closed"}}
    nim = {
        "request_count": 13,
        "retry_count": 8,
        "settings": {"max_attempts_per_request": 1, "read_timeout_seconds": 900.0},
        "pool": {
            "keys": [
                {"key_id": "key-1", "in_flight": 1, "semaphore_locked": True, "success_count": 0, "error_count": 4},
                {"key_id": "key-2", "in_flight": 1, "semaphore_locked": True, "success_count": 0, "error_count": 4},
            ]
        },
    }

    findings = classify_snapshot(_snapshot(smart, nim))

    assert any(item.code == "NIM_KEYS_BUSY" for item in findings)


def test_summarize_samples_computes_deltas() -> None:
    first = _snapshot({"total_requests": 10, "total_errors": 1, "active_requests": 0}, {"request_count": 5, "retry_count": 1, "pool": {"keys": []}})
    last = _snapshot({"total_requests": 13, "total_errors": 2, "active_requests": 1}, {"request_count": 8, "retry_count": 3, "pool": {"keys": []}})

    summary = summarize_samples([first, last])

    assert summary["smart_total_requests_delta"] == 3
    assert summary["smart_total_errors_delta"] == 1
    assert summary["nim_request_count_delta"] == 3
    assert summary["nim_retry_count_delta"] == 2
    assert summary["final_active_requests"] == 1

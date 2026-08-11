#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-11 18:20:00

"""Recommend NVIDIA NIM sidecar tuning from /stats output."""

from __future__ import annotations

import argparse
import json
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class NIMProxyTuningReport:
    status: str
    observed_key_count: int
    current: dict[str, Any]
    recommendations: tuple[str, ...] = field(default_factory=tuple)
    suggested_env: dict[str, str] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def build_tuning_report(stats: dict[str, Any]) -> NIMProxyTuningReport:
    settings = dict(stats.get("settings", {}) or {})
    pool = dict(stats.get("pool", {}) or {})
    keys = list(pool.get("keys", []) or [])
    key_count = int(pool.get("key_count", len(keys)) or 0)
    per_key_rpm = int(settings.get("per_key_rpm", 35) or 35)
    per_key_concurrency = int(settings.get("per_key_concurrency", 1) or 1)
    fallback_count = int(stats.get("fallback_count", 0) or 0)
    enable_fallback = bool(settings.get("enable_fallback", False))
    session_affinity = bool(settings.get("session_affinity", False))

    key_usage = [
        int(key.get("success_count", 0) or 0) + int(key.get("error_count", 0) or 0)
        for key in keys
    ]
    used_key_count = len([item for item in key_usage if item > 0])
    max_key_usage = max(key_usage or [0])
    min_key_usage = min(key_usage or [0])

    cooldown_keys = [key for key in keys if key.get("in_cooldown")]
    error_keys = [key for key in keys if int(key.get("error_count", 0) or 0) > 0]
    high_rpm_keys = [
        key for key in keys
        if int(key.get("recent_rpm", 0) or 0) >= max(1, int(0.9 * per_key_rpm))
    ]
    locked_keys = [key for key in keys if key.get("semaphore_locked")]

    recs: list[str] = []
    env: dict[str, str] = {}

    if key_count < 2:
        recs.append("Add a second personal NVIDIA_API_KEY_2 before increasing RPM.")
    elif used_key_count < key_count and max_key_usage >= 5:
        recs.append("Key usage is imbalanced; disable session affinity and restart so requests spread across keys.")
        env["NIM_PROXY_SESSION_AFFINITY"] = "0"
    if cooldown_keys:
        new_rpm = max(20, min(per_key_rpm - 5, 30))
        recs.append("Keys are in cooldown; reduce RPM and let cooldown finish instead of retrying.")
        env["NIM_PROXY_PER_KEY_RPM"] = str(new_rpm)
        env["NIM_PROXY_DEFAULT_COOLDOWN_SECONDS"] = "600"
    elif high_rpm_keys:
        recs.append("Recent RPM is near the configured cap; keep 10-15% headroom.")
        env["NIM_PROXY_PER_KEY_RPM"] = str(max(20, min(per_key_rpm - 3, 35)))
    if locked_keys or (error_keys and per_key_concurrency > 1):
        recs.append("Concurrency pressure/errors observed; try per-key concurrency 1.")
        env["NIM_PROXY_PER_KEY_CONCURRENCY"] = "1"
    if error_keys:
        env.setdefault("FORGE_REMOTE_MAX_CONCURRENCY", "1")
        recs.append("Upstream errors were observed; keep total remote concurrency 1 for GLM-5.2 slow mode.")
        if not enable_fallback:
            recs.append("Fallback is disabled; keep NIM_PROXY_ENABLE_FALLBACK=0 unless the user explicitly accepts model switching.")
    if fallback_count > 0:
        recs.append("Fallback was used; review quality before keeping fallback enabled.")
    if not recs:
        recs.append("Current NIM proxy stats look healthy; keep current limits and monitor /stats.")

    status = "tune_down" if env else "healthy"
    return NIMProxyTuningReport(
        status=status,
        observed_key_count=key_count,
        current={
            "per_key_rpm": per_key_rpm,
            "per_key_concurrency": per_key_concurrency,
            "fallback_count": fallback_count,
            "session_affinity": session_affinity,
            "used_key_count": used_key_count,
            "max_key_usage": max_key_usage,
            "min_key_usage": min_key_usage,
            "cooldown_key_count": len(cooldown_keys),
            "error_key_count": len(error_keys),
            "high_rpm_key_count": len(high_rpm_keys),
            "locked_key_count": len(locked_keys),
        },
        recommendations=tuple(recs),
        suggested_env=env,
    )


def load_stats_from_url(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=10) as response:  # noqa: S310 - localhost diagnostics
        data = response.read().decode("utf-8")
    payload = json.loads(data)
    if not isinstance(payload, dict):
        raise ValueError("stats endpoint did not return a JSON object")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats-json")
    parser.add_argument("--url", default="http://127.0.0.1:4010/stats")
    args = parser.parse_args()

    if args.stats_json:
        stats = json.loads(Path(args.stats_json).read_text(encoding="utf-8"))
    else:
        stats = load_stats_from_url(args.url)
    report = build_tuning_report(stats)
    print(report.to_json())


if __name__ == "__main__":
    main()

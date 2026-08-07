# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-07 23:20:00

"""NIM proxy tuning recommendation tests."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.diagnostics.nim_proxy_tuning import build_tuning_report  # noqa: E402


def test_tuning_recommends_second_key_when_only_one_key() -> None:
    report = build_tuning_report(
        {
            "settings": {"per_key_rpm": 35, "per_key_concurrency": 2},
            "pool": {"key_count": 1, "keys": []},
        }
    )

    assert report.status == "healthy"
    assert any("second" in item for item in report.recommendations)


def test_tuning_reduces_rpm_on_cooldown() -> None:
    report = build_tuning_report(
        {
            "settings": {"per_key_rpm": 35, "per_key_concurrency": 2},
            "pool": {
                "key_count": 2,
                "keys": [
                    {"key_id": "key-1", "in_cooldown": True, "recent_rpm": 35, "error_count": 3},
                    {"key_id": "key-2", "in_cooldown": False, "recent_rpm": 10, "error_count": 0},
                ],
            },
        }
    )

    assert report.status == "tune_down"
    assert report.suggested_env["NIM_PROXY_PER_KEY_RPM"] == "30"
    assert report.suggested_env["NIM_PROXY_DEFAULT_COOLDOWN_SECONDS"] == "600"


def test_tuning_recommends_concurrency_one_on_errors() -> None:
    report = build_tuning_report(
        {
            "settings": {"per_key_rpm": 30, "per_key_concurrency": 2},
            "pool": {
                "key_count": 2,
                "keys": [
                    {"key_id": "key-1", "in_cooldown": False, "recent_rpm": 5, "error_count": 1},
                ],
            },
        }
    )

    assert report.suggested_env["NIM_PROXY_PER_KEY_CONCURRENCY"] == "1"


def test_tuning_detects_imbalanced_key_usage() -> None:
    report = build_tuning_report(
        {
            "settings": {"per_key_rpm": 35, "per_key_concurrency": 1, "enable_fallback": False},
            "pool": {
                "key_count": 2,
                "keys": [
                    {"key_id": "key-1", "in_cooldown": False, "recent_rpm": 0, "success_count": 30, "error_count": 15},
                    {"key_id": "key-2", "in_cooldown": False, "recent_rpm": 0, "success_count": 0, "error_count": 0},
                ],
            },
        }
    )

    assert report.status == "tune_down"
    assert report.suggested_env["NIM_PROXY_SESSION_AFFINITY"] == "0"
    assert report.suggested_env["FORGE_REMOTE_MAX_CONCURRENCY"] == "2"
    assert report.suggested_env["NIM_PROXY_ENABLE_FALLBACK"] == "1"


def test_tuning_reports_healthy_when_no_pressure() -> None:
    report = build_tuning_report(
        {
            "settings": {"per_key_rpm": 30, "per_key_concurrency": 1},
            "pool": {
                "key_count": 2,
                "keys": [
                    {"key_id": "key-1", "in_cooldown": False, "recent_rpm": 5, "success_count": 5, "error_count": 0},
                    {"key_id": "key-2", "in_cooldown": False, "recent_rpm": 4, "success_count": 4, "error_count": 0},
                ],
            },
        }
    )

    assert report.status == "healthy"
    assert report.suggested_env == {}

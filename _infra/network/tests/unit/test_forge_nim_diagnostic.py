# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-08 12:45:00

"""Tests for FORGE NIM diagnostic runner helpers."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.diagnostics.forge_nim_diagnostic import (  # noqa: E402
    PROFILES,
    make_anthropic_payload,
    make_openai_payload,
    parse_curl_metrics,
    redact_text,
    selected_env_snapshot,
    upsert_env_lines,
)


def test_redact_text_removes_common_secret_shapes() -> None:
    text = (
        "Authorization: Bearer abcdefghijklmnopqrstuvwxyz0123456789\n"
        "NVIDIA_API_KEY_1=nvapi-abcdefghijklmnopqrstuvwxyz0123456789\n"
        "ANTHROPIC_API_KEY=sk-abcdefghijklmnopqrstuvwxyz\n"
    )

    redacted = redact_text(text)

    assert "Bearer <redacted>" in redacted
    assert "nvapi-<redacted>" in redacted
    assert "sk-<redacted>" in redacted
    assert "abcdefghijklmnopqrstuvwxyz0123456789" not in redacted


def test_upsert_env_lines_updates_existing_and_appends_missing() -> None:
    text = "A=1\n# comment\nB=2\n"

    updated = upsert_env_lines(text, {"B": "22", "C": "3"})

    assert "A=1" in updated
    lines = updated.splitlines()
    assert "B=22" in lines
    assert "C=3" in lines
    assert "B=2" not in lines


def test_timeout_a_profile_keeps_fallback_disabled() -> None:
    profile = PROFILES["timeout-a"]

    assert profile["FORGE_USE_NIM_PROXY"] == "1"
    assert profile["NIM_PROXY_READ_TIMEOUT_SECONDS"] == "300"
    assert profile["NIM_PROXY_REQUEST_WALL_TIMEOUT_SECONDS"] == "360"
    assert profile["NIM_PROXY_ENABLE_FALLBACK"] == "0"
    assert profile["FORGE_REMOTE_MAX_CONCURRENCY"] == "1"


def test_glm_slow_profile_is_no_fallback_long_timeout_and_smaller_context() -> None:
    profile = PROFILES["glm-slow"]

    assert profile["FORGE_USE_NIM_PROXY"] == "1"
    assert profile["NIM_PROXY_READ_TIMEOUT_SECONDS"] == "360"
    assert profile["NIM_PROXY_REQUEST_WALL_TIMEOUT_SECONDS"] == "600"
    assert profile["NIM_PROXY_ENABLE_FALLBACK"] == "0"
    assert profile["FORGE_REMOTE_MAX_CONCURRENCY"] == "1"
    assert profile["NIM_PROXY_PER_KEY_CONCURRENCY"] == "1"
    assert profile["FORGE_CTX_SOFT_TOKENS"] == "12000"
    assert profile["FORGE_CTX_KEEP_RECENT_TURNS"] == "4"
    assert profile["FORGE_CTX_TRUNC_TOOL_RESULT_CHARS"] == "800"


def test_payload_builders_embed_trace() -> None:
    openai_payload = make_openai_payload("TRACE-X", "z-ai/glm-5.2")
    anthropic_payload = make_anthropic_payload("TRACE-Y")

    assert openai_payload["model"] == "z-ai/glm-5.2"
    assert openai_payload["stream"] is False
    assert "TRACE-X" in openai_payload["messages"][0]["content"]
    assert anthropic_payload["model"] == "claude-opus-4-8"
    assert "TRACE-Y" in anthropic_payload["messages"][0]["content"]


def test_parse_curl_metrics_parses_numbers_and_strings() -> None:
    metrics = parse_curl_metrics(
        "http_code=504\ntime_total=120.231161\ntime_starttransfer=120.230428\nremote_ip=127.0.0.1\n"
    )

    assert metrics["http_code"] == 504
    assert metrics["time_total"] == 120.231161
    assert metrics["remote_ip"] == "127.0.0.1"


def test_selected_env_snapshot_redacts_indexed_keys(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text(
        "NVIDIA_API_KEY_1=nvapi-secret-secret-secret\n"
        "NIM_PROXY_READ_TIMEOUT_SECONDS=120\n"
        "ANTHROPIC_API_KEY=sk-secret\n",
        encoding="utf-8",
    )

    snap = selected_env_snapshot(tmp_path)

    assert snap["NVIDIA_API_KEY_1"].startswith("<redacted:")
    assert snap["NIM_PROXY_READ_TIMEOUT_SECONDS"] == "120"
    assert snap["ANTHROPIC_API_KEY"].startswith("<redacted:")

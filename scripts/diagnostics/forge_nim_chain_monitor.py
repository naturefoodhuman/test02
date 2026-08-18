#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-19 00:40:00

"""Monitor and classify the FORGE Smart Proxy -> NIM sidecar -> NVIDIA chain.

The script is safe-by-default:
- does not read raw .env values except through selected_env_snapshot() redaction;
- does not send model inference requests unless a future explicit probe flag is added;
- samples only localhost status endpoints and local logs;
- can push a sanitized diagnostics/* artifact branch for remote analysis.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.diagnostics.forge_nim_diagnostic import (  # noqa: E402
    create_tarball,
    local_time,
    push_sanitized_artifact,
    read_json_url,
    redact_text,
    safe_run_text,
    selected_env_snapshot,
)

SMART_URL = "http://127.0.0.1:4000/_forge/status"
SMART_HEALTH_URL = "http://127.0.0.1:4000/_forge/health"
NIM_STATS_URL = "http://127.0.0.1:4010/stats"
NIM_HEALTH_URL = "http://127.0.0.1:4010/healthz"
SMART_LOG = Path("/tmp/forge_smart_proxy.log")
NIM_LOG = Path("/tmp/forge_nim_proxy.log")
REQUEST_EVENT_LOG = Path(os.getenv("FORGE_REQUEST_EVENT_LOG_PATH", "/tmp/forge_request_events.jsonl"))


@dataclass(slots=True)
class ChainFinding:
    level: str
    code: str
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""


@dataclass(slots=True)
class ChainSnapshot:
    local_time: str
    epoch: float
    smart_health: dict[str, Any]
    nim_health: dict[str, Any]
    smart_status: dict[str, Any]
    nim_stats: dict[str, Any]


def _now() -> float:
    return time.time()


def read_tail(path: Path, max_lines: int = 300) -> str:
    if not path.exists():
        return ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:]
        return redact_text("\n".join(lines) + "\n")
    except Exception as exc:  # pragma: no cover - defensive diagnostics
        return f"<failed to read {path}: {type(exc).__name__}: {exc}>\n"


def count_patterns(text: str) -> dict[str, int]:
    patterns = {
        "http_429": r"HTTP/1\.1\" 429|HTTP 429|Too Many Requests",
        "http_503": r"HTTP/1\.1\" 503|HTTP 503",
        "http_504": r"HTTP/1\.1\" 504|HTTP 504|Gateway Timeout",
        "read_timeout": r"ReadTimeout|read operation timed out",
        "remote_protocol_error": r"RemoteProtocolError|incomplete chunked read",
        "no_key_available": r"No NVIDIA NIM key available",
        "busy": r'"type"\s*:\s*"busy"|type=busy|\bbusy\b',
        "rate_limit": r'"type"\s*:\s*"rate_limit"|rate_limit|限流',
        "client_disconnect": r"客户端断开连接|ClientDisconnect|client disconnected",
        "bind_in_use": r"address already in use|Errno 48|Address already in use",
        "context_compacted": r"context budget compacted|上下文.*压缩",
        "context_rejected": r"context budget rejected|context_too_large|超限",
    }
    return {name: len(re.findall(pattern, text, flags=re.IGNORECASE)) for name, pattern in patterns.items()}


def collect_snapshot() -> ChainSnapshot:
    return ChainSnapshot(
        local_time=local_time(),
        epoch=_now(),
        smart_health=read_json_url(SMART_HEALTH_URL, timeout=10),
        nim_health=read_json_url(NIM_HEALTH_URL, timeout=10),
        smart_status=read_json_url(SMART_URL, timeout=10),
        nim_stats=read_json_url(NIM_STATS_URL, timeout=10),
    )


def key_states(nim_stats: dict[str, Any]) -> list[dict[str, Any]]:
    pool = nim_stats.get("pool") if isinstance(nim_stats.get("pool"), dict) else {}
    keys = pool.get("keys") if isinstance(pool.get("keys"), list) else []
    return [item for item in keys if isinstance(item, dict)]


def total_key_value(keys: list[dict[str, Any]], name: str) -> int:
    return sum(int(key.get(name, 0) or 0) for key in keys)


def classify_snapshot(snapshot: ChainSnapshot, smart_log_tail: str = "", nim_log_tail: str = "", request_events_tail: str = "") -> list[ChainFinding]:
    findings: list[ChainFinding] = []
    smart = snapshot.smart_status if isinstance(snapshot.smart_status, dict) else {}
    nim = snapshot.nim_stats if isinstance(snapshot.nim_stats, dict) else {}
    settings = nim.get("settings") if isinstance(nim.get("settings"), dict) else {}
    keys = key_states(nim)
    active_requests = int(smart.get("active_requests", 0) or 0)
    smart_total = int(smart.get("total_requests", 0) or 0)
    smart_errors = int(smart.get("total_errors", 0) or 0)
    nim_request_count = int(nim.get("request_count", 0) or 0)
    nim_retry_count = int(nim.get("retry_count", 0) or 0)
    fallback_enabled = bool(settings.get("enable_fallback", False))
    max_attempts = int(settings.get("max_attempts_per_request", 0) or 0)
    read_timeout = float(settings.get("read_timeout_seconds", 0) or 0)
    wall_timeout = float(settings.get("request_wall_timeout_seconds", 0) or 0)


    active_items = smart.get("requests") if isinstance(smart.get("requests"), list) else []
    stale_waiting = [
        item for item in active_items
        if isinstance(item, dict)
        and float(item.get("elapsed_s", 0) or 0) >= 900
        and int(item.get("bytes", 0) or 0) == 0
    ]
    if stale_waiting:
        findings.append(
            ChainFinding(
                level="high",
                code="SMART_STALE_WAITING_REQUESTS",
                message="Smart Proxy has long-running waiting requests with no model bytes emitted.",
                evidence={"requests": stale_waiting[:10]},
                recommendation=(
                    "Pull latest code with FORGE_REMOTE_OPERATION_TIMEOUT_SECONDS and tracker stale pruning; "
                    "restart 4000/4010. These requests are usually queued/non-stream waits, not useful model output."
                ),
            )
        )

    if snapshot.smart_health.get("_error") or snapshot.nim_health.get("_error"):
        findings.append(
            ChainFinding(
                level="critical",
                code="LOCAL_SERVICE_UNHEALTHY",
                message="4000 Smart Proxy or 4010 NIM sidecar health endpoint is not reachable.",
                evidence={"smart_health": snapshot.smart_health, "nim_health": snapshot.nim_health},
                recommendation="Restart only 4000/4010 with `python3 scripts/diagnostics/forge_nim_diagnostic.py --restart`.",
            )
        )

    in_flight = total_key_value(keys, "in_flight")
    locked_keys = [key for key in keys if key.get("semaphore_locked") or int(key.get("in_flight", 0) or 0) > 0]
    cooldown_keys = [key for key in keys if key.get("in_cooldown")]
    consecutive_429 = total_key_value(keys, "consecutive_429")
    key_success = total_key_value(keys, "success_count")
    key_errors = total_key_value(keys, "error_count")

    if cooldown_keys or consecutive_429 > 0:
        findings.append(
            ChainFinding(
                level="high",
                code="NVIDIA_UPSTREAM_429_COOLDOWN",
                message="At least one NVIDIA key is in cooldown or has consecutive upstream 429s.",
                evidence={
                    "cooldown_keys": [
                        {
                            "key_id": key.get("key_id"),
                            "available_in_seconds": key.get("available_in_seconds"),
                            "consecutive_429": key.get("consecutive_429"),
                        }
                        for key in cooldown_keys
                    ],
                    "total_consecutive_429": consecutive_429,
                },
                recommendation=(
                    "Treat this as upstream NVIDIA/free-tier pressure. Keep fallback disabled if policy requires it; "
                    "reduce prompt size and keep FORGE_REMOTE_MAX_CONCURRENCY=1. Do not increase RPM."
                ),
            )
        )

    if locked_keys:
        findings.append(
            ChainFinding(
                level="medium",
                code="NIM_KEYS_BUSY",
                message="One or more NIM keys are occupied by long-running upstream requests.",
                evidence={
                    "in_flight_total": in_flight,
                    "locked_keys": [
                        {
                            "key_id": key.get("key_id"),
                            "in_flight": key.get("in_flight"),
                            "success_count": key.get("success_count"),
                            "error_count": key.get("error_count"),
                        }
                        for key in locked_keys
                    ],
                },
                recommendation=(
                    "This is expected when GLM-5.2 takes minutes. Ensure NIM_PROXY_MAX_ATTEMPTS_PER_REQUEST=1 "
                    "and consider NIM_PROXY_QUEUE_TIMEOUT_SECONDS=120 so new turns fail fast with busy instead of waiting forever."
                ),
            )
        )

    retry = smart.get("retry") if isinstance(smart.get("retry"), dict) else {}
    retry_counters = retry.get("retry_counters") if isinstance(retry.get("retry_counters"), dict) else {}
    smart_429_count = int(retry_counters.get("429", 0) or 0)
    if smart_429_count > 0:
        findings.append(
            ChainFinding(
                level="high",
                code="SMART_SEES_429_FROM_NIM",
                message="Smart Proxy has observed 429 responses from the NIM sidecar.",
                evidence={"smart_retry_429_counter": smart_429_count},
                recommendation=(
                    "If running a version before abd6459, pull latest: NIM busy should be separated from true rate_limit. "
                    "If still 429 after latest, inspect 4010 /stats cooldown fields."
                ),
            )
        )

    circuit = smart.get("circuit_breaker") if isinstance(smart.get("circuit_breaker"), dict) else {}
    if circuit.get("state") == "open":
        findings.append(
            ChainFinding(
                level="high",
                code="SMART_CIRCUIT_OPEN",
                message="Smart Proxy circuit breaker is open.",
                evidence=circuit,
                recommendation="Pull latest abd6459+ so NIM sidecar local busy does not trip global circuit breaker; restart 4000/4010.",
            )
        )

    context = smart.get("context_budget") if isinstance(smart.get("context_budget"), dict) else {}
    last_context = context.get("last") if isinstance(context.get("last"), dict) else {}
    est_before = int(last_context.get("est_before", 0) or 0)
    soft_tokens = int(context.get("soft_tokens", 0) or 0)
    max_tokens = int(context.get("max_tokens", 0) or 0)
    if est_before and soft_tokens and est_before >= soft_tokens:
        findings.append(
            ChainFinding(
                level="medium",
                code="PROMPT_LARGE_OR_COMPACTED",
                message="Prompt/context is large enough to trigger or approach compaction.",
                evidence={"est_before": est_before, "soft_tokens": soft_tokens, "max_tokens": max_tokens, "last_context": last_context},
                recommendation="Large prompts increase GLM-5.2 latency and 429 risk. If failures persist, reduce FORGE_CTX_SOFT_TOKENS or run /compact in Claude Code.",
            )
        )

    if max_attempts > 1 and read_timeout >= 600:
        findings.append(
            ChainFinding(
                level="high",
                code="LONG_TIMEOUT_WITH_MULTIPLE_ATTEMPTS",
                message="Long read timeout is combined with multiple attempts, which can occupy keys for a very long time.",
                evidence={"read_timeout_seconds": read_timeout, "request_wall_timeout_seconds": wall_timeout, "max_attempts_per_request": max_attempts},
                recommendation="Set NIM_PROXY_MAX_ATTEMPTS_PER_REQUEST=1 when read_timeout is 900+ seconds.",
            )
        )

    log_counts = {"smart": count_patterns(smart_log_tail), "nim": count_patterns(nim_log_tail)}
    if log_counts["smart"].get("bind_in_use", 0) > 0:
        findings.append(
            ChainFinding(
                level="medium",
                code="SMART_BIND_CONFLICT_IN_LOGS",
                message="Smart Proxy logs include address-in-use errors.",
                evidence=log_counts["smart"],
                recommendation="Use the latest diagnostic restart, which verifies listener PID ownership, then restart 4000/4010.",
            )
        )
    if log_counts["nim"].get("read_timeout", 0) or log_counts["smart"].get("read_timeout", 0):
        findings.append(
            ChainFinding(
                level="medium",
                code="READ_TIMEOUT_IN_LOGS",
                message="Recent logs include ReadTimeout events.",
                evidence=log_counts,
                recommendation="This usually indicates NVIDIA GLM-5.2 slow/overloaded responses. Long timeout may help but cannot guarantee success.",
            )
        )

    if request_events_tail:
        req_counts = count_patterns(request_events_tail)
        if "request_stale_pruned" in request_events_tail or "no_output" in request_events_tail:
            findings.append(
                ChainFinding(
                    level="medium",
                    code="REQUEST_EVENT_AUTO_CONTINUE_ACTIVITY",
                    message="Request event log contains auto-continue/no-output/stale-prune activity.",
                    evidence={"pattern_counts": req_counts},
                    recommendation="Inspect /tmp/forge_request_events.jsonl or the artifact request_events_tail.log for per-turn timing.",
                )
            )

    if smart_total and nim_request_count == 0:
        findings.append(
            ChainFinding(
                level="high",
                code="SMART_NOT_REACHING_NIM",
                message="Smart Proxy has requests but NIM sidecar request_count is zero.",
                evidence={"smart_total_requests": smart_total, "nim_request_count": nim_request_count},
                recommendation="Check FORGE_USE_NIM_PROXY, NIM_PROXY_BASE_URL, and 4010 health.",
            )
        )

    if not findings:
        findings.append(
            ChainFinding(
                level="info",
                code="NO_LOCAL_CHAIN_ISSUE_DETECTED",
                message="No obvious local 4000/4010 configuration issue detected in the current snapshot.",
                evidence={
                    "smart_total_requests": smart_total,
                    "smart_total_errors": smart_errors,
                    "nim_request_count": nim_request_count,
                    "nim_retry_count": nim_retry_count,
                    "key_success": key_success,
                    "key_errors": key_errors,
                    "fallback_enabled": fallback_enabled,
                },
                recommendation="If Claude Code is still waiting, it is likely waiting on NVIDIA GLM-5.2 upstream latency.",
            )
        )
    return findings


def summarize_samples(samples: list[ChainSnapshot]) -> dict[str, Any]:
    if not samples:
        return {}
    first = samples[0]
    last = samples[-1]
    first_smart = first.smart_status if isinstance(first.smart_status, dict) else {}
    last_smart = last.smart_status if isinstance(last.smart_status, dict) else {}
    first_nim = first.nim_stats if isinstance(first.nim_stats, dict) else {}
    last_nim = last.nim_stats if isinstance(last.nim_stats, dict) else {}
    return {
        "sample_count": len(samples),
        "started_local": first.local_time,
        "ended_local": last.local_time,
        "smart_total_requests_delta": int(last_smart.get("total_requests", 0) or 0) - int(first_smart.get("total_requests", 0) or 0),
        "smart_total_errors_delta": int(last_smart.get("total_errors", 0) or 0) - int(first_smart.get("total_errors", 0) or 0),
        "nim_request_count_delta": int(last_nim.get("request_count", 0) or 0) - int(first_nim.get("request_count", 0) or 0),
        "nim_retry_count_delta": int(last_nim.get("retry_count", 0) or 0) - int(first_nim.get("retry_count", 0) or 0),
        "final_active_requests": last_smart.get("active_requests"),
        "final_keys": key_states(last_nim),
    }


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def collect_static_context(root: Path, output_dir: Path) -> None:
    write_json(
        output_dir / "static_context.json",
        {
            "local_time": local_time(),
            "root": str(root),
            "git_log": safe_run_text(["git", "log", "--oneline", "--decorate", "-10"], cwd=root),
            "git_status": safe_run_text(["git", "status", "--short", "--branch"], cwd=root),
            "selected_env": selected_env_snapshot(root),
            "env_proxy": safe_run_text(["bash", "-lc", "env | grep -Ei 'proxy|all_proxy|http_proxy|https_proxy|no_proxy' || true"], cwd=root),
            "macos_proxy": safe_run_text(["bash", "-lc", "scutil --proxy || true"], cwd=root),
            "ports": safe_run_text(
                [
                    "bash",
                    "-lc",
                    "lsof -nP -iTCP:4000 -sTCP:LISTEN; lsof -nP -iTCP:4010 -sTCP:LISTEN; "
                    "lsof -nP -iTCP:8080 -sTCP:LISTEN; lsof -nP -iTCP:1080 -sTCP:LISTEN; "
                    "lsof -nP -iTCP:1087 -sTCP:LISTEN; lsof -nP -iTCP:11085 -sTCP:LISTEN",
                ],
                cwd=root,
            ),
            "request_event_log_path": str(REQUEST_EVENT_LOG),
            "pid_files": {
                "smart": Path("/tmp/forge_smart_proxy.pid").read_text(encoding="utf-8", errors="replace").strip()
                if Path("/tmp/forge_smart_proxy.pid").exists()
                else "",
                "nim": Path("/tmp/forge_nim_proxy.pid").read_text(encoding="utf-8", errors="replace").strip()
                if Path("/tmp/forge_nim_proxy.pid").exists()
                else "",
            },
        },
    )


def render_summary(
    output_dir: Path,
    snapshot: ChainSnapshot,
    findings: list[ChainFinding],
    sample_summary: dict[str, Any],
) -> str:
    lines = [
        "# FORGE NIM Chain Monitor Summary",
        "",
        f"- generated_local: `{local_time()}`",
        f"- output_dir: `{output_dir}`",
        "",
        "## Findings",
        "",
    ]
    for item in findings:
        lines.extend(
            [
                f"### {item.level.upper()} — {item.code}",
                "",
                item.message,
                "",
                f"Recommendation: {item.recommendation}",
                "",
                "```json",
                json.dumps(item.evidence, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Sample summary",
            "",
            "```json",
            json.dumps(sample_summary, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Latest snapshot excerpt",
            "",
            "```json",
            json.dumps(
                {
                    "smart": {
                        "active_requests": snapshot.smart_status.get("active_requests"),
                        "total_requests": snapshot.smart_status.get("total_requests"),
                        "total_errors": snapshot.smart_status.get("total_errors"),
                        "retry": snapshot.smart_status.get("retry"),
                        "circuit_breaker": snapshot.smart_status.get("circuit_breaker"),
                        "context_budget": snapshot.smart_status.get("context_budget"),
                    },
                    "nim": {
                        "request_count": snapshot.nim_stats.get("request_count"),
                        "retry_count": snapshot.nim_stats.get("retry_count"),
                        "settings": snapshot.nim_stats.get("settings"),
                        "pool": snapshot.nim_stats.get("pool"),
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Monitor FORGE Smart Proxy / NIM / NVIDIA runtime chain")
    parser.add_argument("--root", default=os.getcwd())
    parser.add_argument("--duration", type=int, default=0, help="Seconds to sample. 0 means one snapshot only.")
    parser.add_argument("--interval", type=int, default=15)
    parser.add_argument("--tail-lines", type=int, default=500)
    parser.add_argument("--push-sanitized-artifact", action="store_true")
    parser.add_argument("--artifact-branch", default=None)
    parser.add_argument("--output-base", default="/tmp")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    root = Path(args.root).expanduser().resolve()
    output_dir = Path(args.output_base).expanduser().resolve() / f"forge_nim_chain_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir.mkdir(parents=True, exist_ok=False)
    print(f"CHAIN_OUTPUT_DIR={output_dir}")
    print(f"ROOT={root}")
    print(f"DURATION={args.duration}")
    print(f"INTERVAL={args.interval}")

    collect_static_context(root, output_dir)
    samples: list[ChainSnapshot] = []
    deadline = _now() + max(0, args.duration)
    while True:
        snapshot = collect_snapshot()
        samples.append(snapshot)
        with (output_dir / "samples.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(snapshot), ensure_ascii=False) + "\n")
        if args.duration <= 0 or _now() >= deadline:
            break
        time.sleep(max(1, args.interval))

    latest = samples[-1]
    smart_tail = read_tail(SMART_LOG, args.tail_lines)
    nim_tail = read_tail(NIM_LOG, args.tail_lines)
    request_events_tail = read_tail(REQUEST_EVENT_LOG, args.tail_lines)
    write_text(output_dir / "forge_smart_proxy_tail.log", smart_tail)
    write_text(output_dir / "forge_nim_proxy_tail.log", nim_tail)
    write_text(output_dir / "request_events_tail.log", request_events_tail)
    write_json(output_dir / "log_pattern_counts.json", {"smart": count_patterns(smart_tail), "nim": count_patterns(nim_tail), "request_events": count_patterns(request_events_tail)})

    findings = classify_snapshot(latest, smart_tail, nim_tail, request_events_tail)
    sample_summary = summarize_samples(samples)
    write_json(output_dir / "findings.json", [asdict(item) for item in findings])
    write_json(output_dir / "sample_summary.json", sample_summary)
    write_text(output_dir / "SUMMARY.md", render_summary(output_dir, latest, findings, sample_summary))
    tarball = create_tarball(output_dir)

    pushed_branch = ""
    push_failed = ""
    if args.push_sanitized_artifact:
        try:
            pushed_branch = push_sanitized_artifact(root, output_dir, branch=args.artifact_branch)
            write_text(output_dir / "PUSHED_BRANCH.txt", pushed_branch + "\n")
        except Exception as exc:
            push_failed = f"{type(exc).__name__}: {exc}"
            write_text(output_dir / "PUSH_FAILED.txt", push_failed + "\n")

    print("\nDONE")
    print(f"CHAIN_OUTPUT_DIR={output_dir}")
    print(f"CHAIN_TARBALL={tarball}")
    if pushed_branch:
        print(f"PUSHED_BRANCH={pushed_branch}")
    if push_failed:
        print(f"PUSH_FAILED={push_failed}")
        print(f"PUSH_LOG={output_dir / 'push_sanitized_artifact.log'}")
    print("FINDINGS=" + json.dumps([asdict(item) for item in findings], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

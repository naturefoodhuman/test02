#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-09 10:20:00

"""FORGE Smart Proxy / NIM sidecar diagnostic runner.

This script is intentionally behavior-neutral by default: it collects evidence
and runs minimal probes. It can optionally apply an env-only test profile,
restart local services, and push a sanitized artifact branch for remote analysis.

No third-party dependencies are required.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SENSITIVE_ENV_ALLOWLIST = {
    "FORGE_USE_NIM_PROXY",
    "NIM_PROXY_HOST",
    "NIM_PROXY_PORT",
    "NIM_PROXY_BASE_URL",
    "NIM_PROXY_PER_KEY_RPM",
    "NIM_PROXY_PER_KEY_CONCURRENCY",
    "NIM_PROXY_DEFAULT_COOLDOWN_SECONDS",
    "NIM_PROXY_RETRY_AFTER_CAP_SECONDS",
    "NIM_PROXY_QUEUE_TIMEOUT_SECONDS",
    "NIM_PROXY_READ_TIMEOUT_SECONDS",
    "NIM_PROXY_REQUEST_WALL_TIMEOUT_SECONDS",
    "NIM_PROXY_MAX_ATTEMPTS_PER_REQUEST",
    "NIM_PROXY_SESSION_AFFINITY",
    "NIM_PROXY_ENABLE_FALLBACK",
    "NIM_PRIMARY_MODEL",
    "NIM_FALLBACK_MODEL",
    "FORGE_REMOTE_MAX_CONCURRENCY",
    "FORGE_CTX_SOFT_TOKENS",
    "FORGE_CTX_KEEP_RECENT_TURNS",
    "FORGE_CTX_TRUNC_TOOL_RESULT_CHARS",
    "FORGE_REMOTE_TOOL_SELECTION",
    "FORGE_REMOTE_SELECTOR_PORT",
    "FORGE_TOOL_SELECTION_MAX",
    "FORGE_TOOL_SCHEMA_BYTE_BUDGET",
}

SECRET_KEY_RE = re.compile(r"(?i)(api[_-]?key|token|secret|authorization|bearer|password)")
BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{12,}")
SK_RE = re.compile(r"sk-[A-Za-z0-9._~+/=-]{8,}")
NVAPI_RE = re.compile(r"nvapi-[A-Za-z0-9._~+/=-]{8,}")
LONG_SECRET_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9_\-]{48,}(?![A-Za-z0-9])")

PROFILES: dict[str, dict[str, str]] = {
    "current": {},
    "timeout-a": {
        "FORGE_USE_NIM_PROXY": "1",
        "NIM_PROXY_READ_TIMEOUT_SECONDS": "300",
        "NIM_PROXY_REQUEST_WALL_TIMEOUT_SECONDS": "360",
        "NIM_PROXY_MAX_ATTEMPTS_PER_REQUEST": "1",
        "NIM_PROXY_ENABLE_FALLBACK": "0",
        "FORGE_REMOTE_MAX_CONCURRENCY": "1",
        "NIM_PROXY_PER_KEY_CONCURRENCY": "1",
    },
    "glm-slow": {
        "FORGE_USE_NIM_PROXY": "1",
        "NIM_PROXY_READ_TIMEOUT_SECONDS": "360",
        "NIM_PROXY_REQUEST_WALL_TIMEOUT_SECONDS": "600",
        "NIM_PROXY_MAX_ATTEMPTS_PER_REQUEST": "1",
        "NIM_PROXY_ENABLE_FALLBACK": "0",
        "FORGE_REMOTE_MAX_CONCURRENCY": "1",
        "NIM_PROXY_PER_KEY_CONCURRENCY": "1",
        "FORGE_CTX_SOFT_TOKENS": "12000",
        "FORGE_CTX_KEEP_RECENT_TURNS": "4",
        "FORGE_CTX_TRUNC_TOOL_RESULT_CHARS": "800",
    },
    "context-c": {
        "NIM_PROXY_ENABLE_FALLBACK": "0",
        "FORGE_CTX_SOFT_TOKENS": "12000",
        "FORGE_CTX_KEEP_RECENT_TURNS": "4",
        "FORGE_CTX_TRUNC_TOOL_RESULT_CHARS": "800",
    },
    "timeout-a-context-c": {
        "FORGE_USE_NIM_PROXY": "1",
        "NIM_PROXY_READ_TIMEOUT_SECONDS": "300",
        "NIM_PROXY_REQUEST_WALL_TIMEOUT_SECONDS": "360",
        "NIM_PROXY_MAX_ATTEMPTS_PER_REQUEST": "1",
        "NIM_PROXY_ENABLE_FALLBACK": "0",
        "FORGE_REMOTE_MAX_CONCURRENCY": "1",
        "NIM_PROXY_PER_KEY_CONCURRENCY": "1",
        "FORGE_CTX_SOFT_TOKENS": "12000",
        "FORGE_CTX_KEEP_RECENT_TURNS": "4",
        "FORGE_CTX_TRUNC_TOOL_RESULT_CHARS": "800",
    },
}


def local_time() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def now_epoch() -> float:
    return time.time()


def redact_text(text: str) -> str:
    text = BEARER_RE.sub("Bearer <redacted>", text)
    text = SK_RE.sub("sk-<redacted>", text)
    text = NVAPI_RE.sub("nvapi-<redacted>", text)
    text = LONG_SECRET_RE.sub(lambda m: f"<redacted:{len(m.group(0))}>", text)
    return text


def run_cmd(
    args: list[str],
    *,
    cwd: Path,
    timeout: float | None = None,
    input_text: str | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd),
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=check,
    )




def run_checked_logged(
    args: list[str],
    *,
    cwd: Path,
    log_path: Path,
    timeout: float = 120,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        env=env,
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"$ {' '.join(args)}\n")
        handle.write(f"exit_code={result.returncode}\n")
        if result.stdout:
            handle.write("[stdout]\n" + redact_text(result.stdout) + "\n")
        if result.stderr:
            handle.write("[stderr]\n" + redact_text(result.stderr) + "\n")
        handle.write("\n")
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, args, result.stdout, result.stderr)
    return result

def safe_run_text(args: list[str], *, cwd: Path, timeout: float = 30) -> str:
    try:
        result = run_cmd(args, cwd=cwd, timeout=timeout)
    except Exception as exc:  # pragma: no cover - defensive diagnostics
        return f"<command failed: {type(exc).__name__}: {exc}>\n"
    combined = ""
    if result.stdout:
        combined += result.stdout
    if result.stderr:
        combined += "\n[stderr]\n" + result.stderr
    return redact_text(combined)


def read_json_url(url: str, timeout: float = 15) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 - localhost diagnostics
            raw = response.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        return data if isinstance(data, dict) else {"raw": data}
    except Exception as exc:
        return {"_error": f"{type(exc).__name__}: {exc}"}


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for _ in handle)


def tail_from_line(path: Path, start_line_1_based: int) -> str:
    if not path.exists():
        return ""
    out: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for idx, line in enumerate(handle, start=1):
            if idx >= start_line_1_based:
                out.append(line)
    return redact_text("".join(out))


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def selected_env_snapshot(root: Path) -> dict[str, str]:
    env_values = parse_env_file(root / ".env")
    selected: dict[str, str] = {}
    for key, value in sorted(env_values.items()):
        if key.startswith("NVIDIA_API_KEY_"):
            selected[key] = f"<redacted:{len(value)}>"
        elif key in SENSITIVE_ENV_ALLOWLIST:
            selected[key] = redact_text(value)
        elif SECRET_KEY_RE.search(key):
            selected[key] = f"<redacted:{len(value)}>"
    return selected


def upsert_env_lines(text: str, updates: dict[str, str]) -> str:
    lines = text.splitlines()
    seen: set[str] = set()
    out: list[str] = []
    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            out.append(raw)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            out.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            out.append(raw)
    for key, value in updates.items():
        if key not in seen:
            out.append(f"{key}={value}")
    return "\n".join(out) + "\n"


def apply_profile(root: Path, profile: str, output_dir: Path) -> dict[str, str]:
    updates = dict(PROFILES[profile])
    if not updates:
        return {}
    env_path = root / ".env"
    original = env_path.read_text(encoding="utf-8", errors="replace") if env_path.exists() else ""
    backup_path = output_dir / f"env_backup_before_{profile}.env.redacted.txt"
    backup_path.write_text(redact_text(original), encoding="utf-8")
    raw_backup_path = Path("/tmp") / f"forge_env_backup_before_{profile}_{output_dir.name}.env"
    raw_backup_path.write_text(original, encoding="utf-8")
    raw_backup_marker = output_dir / f"env_backup_before_{profile}.raw_backup_path.txt"
    raw_backup_marker.write_text(str(raw_backup_path), encoding="utf-8")
    env_path.write_text(upsert_env_lines(original, updates), encoding="utf-8")
    return updates


def truncate_logs() -> None:
    for path in (Path("/tmp/forge_smart_proxy.log"), Path("/tmp/forge_nim_proxy.log")):
        try:
            path.write_text("", encoding="utf-8")
        except Exception:
            pass


def kill_processes(root: Path, output_dir: Path) -> None:
    commands = [
        "pids=$(pgrep -f 'scripts/forge-start.sh' 2>/dev/null); [ -n \"$pids\" ] && kill -9 $pids || true",
        "pids=$(pgrep -f '_infra/smart_proxy.py' 2>/dev/null); [ -n \"$pids\" ] && kill -9 $pids || true",
        "pids=$(pgrep -f '_infra/nim_proxy.py' 2>/dev/null); [ -n \"$pids\" ] && kill -9 $pids || true",
        "pids=$(lsof -tiTCP:4000 -sTCP:LISTEN 2>/dev/null); [ -n \"$pids\" ] && kill -9 $pids || true",
        "pids=$(lsof -tiTCP:4010 -sTCP:LISTEN 2>/dev/null); [ -n \"$pids\" ] && kill -9 $pids || true",
    ]
    log = output_dir / "restart_kill.log"
    chunks: list[str] = []
    for command in commands:
        result = run_cmd(["bash", "-lc", command], cwd=root, timeout=30)
        chunks.append(f"$ {command}\n{result.stdout}{result.stderr}\n")
    log.write_text(redact_text("\n".join(chunks)), encoding="utf-8")


def wait_json_url(url: str, *, timeout_s: float, interval_s: float = 0.5) -> tuple[bool, dict[str, Any]]:
    deadline = time.time() + timeout_s
    last: dict[str, Any] = {}
    while time.time() < deadline:
        last = read_json_url(url, timeout=min(5, max(1, int(interval_s + 1))))
        if last and not last.get("_error"):
            return True, last
        time.sleep(interval_s)
    return False, last


def _popen_detached(
    args: list[str],
    *,
    cwd: Path,
    log_path: Path,
    env: dict[str, str] | None = None,
) -> subprocess.Popen[Any]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("ab", buffering=0)
    try:
        return subprocess.Popen(
            args,
            cwd=str(cwd),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            env=env,
            close_fds=True,
            start_new_session=True,
        )
    finally:
        # The child process owns the duplicated fd; close the parent's handle.
        log_handle.close()


def _python_bin(root: Path) -> str:
    venv_python = root / ".venv" / "bin" / "python"
    if venv_python.exists() and os.access(venv_python, os.X_OK):
        return str(venv_python)
    return shutil.which("python3") or sys.executable


def restart_services_fast(root: Path, output_dir: Path, timeout: int) -> None:
    """Restart only NIM sidecar and Smart Proxy; skip forge-start full model self-check.

    The diagnostic probes only need ports 4010 and 4000. The full forge-start.sh
    script cold-starts local model ports for self-check and can legitimately take
    many minutes, which makes timeout experiments look stuck before probes run.
    """

    kill_processes(root, output_dir)
    truncate_logs()
    start = time.time()
    events: list[dict[str, Any]] = []

    nim_log = Path("/tmp/forge_nim_proxy.log")
    smart_log = Path("/tmp/forge_smart_proxy.log")

    nim_proc = _popen_detached(["bash", "scripts/start-nim-proxy.sh"], cwd=root, log_path=nim_log)
    events.append({"event": "nim_start", "pid": nim_proc.pid, "local_time": local_time()})
    Path("/tmp/forge_nim_proxy.pid").write_text(str(nim_proc.pid), encoding="utf-8")
    ok, payload = wait_json_url("http://127.0.0.1:4010/healthz", timeout_s=45)
    events.append({"event": "nim_health", "ok": ok, "payload": payload, "local_time": local_time()})
    if not ok:
        events.append({"event": "nim_log_tail", "tail": tail_from_line(nim_log, max(1, line_count(nim_log) - 80))})
        (output_dir / "restart_fast.json").write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
        raise RuntimeError("NIM sidecar did not become healthy on 4010 within 45s")

    smart_proc = _popen_detached([_python_bin(root), "_infra/smart_proxy.py"], cwd=root, log_path=smart_log)
    events.append({"event": "smart_start", "pid": smart_proc.pid, "local_time": local_time()})
    Path("/tmp/forge_smart_proxy.pid").write_text(str(smart_proc.pid), encoding="utf-8")
    ok, payload = wait_json_url("http://127.0.0.1:4000/_forge/health", timeout_s=45)
    events.append({"event": "smart_health", "ok": ok, "payload": payload, "local_time": local_time()})
    if not ok:
        events.append({"event": "smart_log_tail", "tail": tail_from_line(smart_log, max(1, line_count(smart_log) - 80))})
        (output_dir / "restart_fast.json").write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
        raise RuntimeError("Smart Proxy did not become healthy on 4000 within 45s")

    events.append({"event": "restart_done", "elapsed_s": round(time.time() - start, 3), "local_time": local_time()})
    (output_dir / "restart_fast.json").write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")


def restart_services_full(root: Path, output_dir: Path, timeout: int) -> None:
    kill_processes(root, output_dir)
    truncate_logs()
    start = time.time()
    try:
        result = run_cmd(["bash", "scripts/forge-start.sh"], cwd=root, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        (output_dir / "restart_timeout.txt").write_text(str(exc), encoding="utf-8")
        raise
    elapsed = time.time() - start
    (output_dir / "restart_forge_start.log").write_text(
        redact_text(
            f"start_local={local_time()}\nelapsed_s={elapsed:.3f}\nexit_code={result.returncode}\n\n"
            f"[stdout]\n{result.stdout}\n\n[stderr]\n{result.stderr}\n"
        ),
        encoding="utf-8",
    )


def restart_services(root: Path, output_dir: Path, timeout: int, mode: str = "fast") -> None:
    if mode == "full":
        restart_services_full(root, output_dir, timeout)
    else:
        restart_services_fast(root, output_dir, timeout)


def snapshot(root: Path, name: str, output_dir: Path) -> dict[str, Any]:
    data = {
        "snapshot": name,
        "local_time": local_time(),
        "epoch": now_epoch(),
        "root": str(root),
        "git_log": safe_run_text(["git", "log", "--oneline", "--decorate", "-8"], cwd=root),
        "git_status": safe_run_text(["git", "status", "--short", "--branch"], cwd=root),
        "smart_pid_file": Path("/tmp/forge_smart_proxy.pid").read_text(encoding="utf-8", errors="replace").strip()
        if Path("/tmp/forge_smart_proxy.pid").exists()
        else "",
        "ps_smart": safe_run_text(
            ["bash", "-lc", "[ -f /tmp/forge_smart_proxy.pid ] && ps -p $(cat /tmp/forge_smart_proxy.pid) -o pid,lstart,etime,command || true"],
            cwd=root,
        ),
        "lsof_4000": safe_run_text(["bash", "-lc", "lsof -nP -iTCP:4000 -sTCP:LISTEN 2>/dev/null || true"], cwd=root),
        "lsof_4010": safe_run_text(["bash", "-lc", "lsof -nP -iTCP:4010 -sTCP:LISTEN 2>/dev/null || true"], cwd=root),
        "health_4010": read_json_url("http://127.0.0.1:4010/healthz"),
        "stats_4010": read_json_url("http://127.0.0.1:4010/stats"),
        "status_4000": read_json_url("http://127.0.0.1:4000/_forge/status"),
        "selected_env": selected_env_snapshot(root),
    }
    (output_dir / f"{name}_snapshot.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def make_openai_payload(trace: str, model: str, stream: bool = False) -> dict[str, Any]:
    return {
        "model": model,
        "stream": stream,
        "max_tokens": 64,
        "messages": [
            {"role": "user", "content": f"{trace} 现在北京时间是多少？只回答一句。"},
        ],
    }


def make_anthropic_payload(trace: str) -> dict[str, Any]:
    return {
        "model": "claude-opus-4-8",
        "max_tokens": 64,
        "messages": [
            {"role": "user", "content": f"{trace} 现在北京时间是多少？只回答一句。"},
        ],
    }


def parse_curl_metrics(text: str) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        try:
            metrics[key] = float(value) if "." in value else int(value)
        except ValueError:
            metrics[key] = value
    return metrics


@dataclass(slots=True)
class ProbeResult:
    name: str
    trace: str
    start_local: str
    end_local: str
    elapsed_s: float
    metrics: dict[str, Any]
    response_preview: str
    smart_delta_path: str
    nim_delta_path: str


def curl_probe(
    root: Path,
    output_dir: Path,
    *,
    name: str,
    url: str,
    payload: dict[str, Any],
    headers: list[str],
    curl_max_time: int,
) -> ProbeResult:
    smart_log = Path("/tmp/forge_smart_proxy.log")
    nim_log = Path("/tmp/forge_nim_proxy.log")
    smart0 = line_count(smart_log)
    nim0 = line_count(nim_log)
    trace = str(payload["messages"][0]["content"]).split()[0]
    prefix = output_dir / name
    payload_path = prefix.with_suffix(".payload.json")
    response_path = prefix.with_suffix(".response.json")
    metrics_path = prefix.with_suffix(".curl_metrics.txt")
    stderr_path = prefix.with_suffix(".curl_stderr.txt")
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    cmd = ["curl", "-sS", "--max-time", str(curl_max_time), "-o", str(response_path)]
    for header in headers:
        cmd.extend(["-H", header])
    cmd.extend([
        "-w",
        "http_code=%{http_code}\ntime_total=%{time_total}\ntime_starttransfer=%{time_starttransfer}\nremote_ip=%{remote_ip}\n",
        url,
        "--data-binary",
        f"@{payload_path}",
    ])
    start = time.time()
    start_local = local_time()
    result = run_cmd(cmd, cwd=root, timeout=curl_max_time + 30)
    elapsed = time.time() - start
    end_local = local_time()
    metrics_path.write_text(redact_text(result.stdout), encoding="utf-8")
    stderr_path.write_text(redact_text(result.stderr), encoding="utf-8")
    if response_path.exists():
        response_text = redact_text(response_path.read_text(encoding="utf-8", errors="replace"))
        response_path.write_text(response_text, encoding="utf-8")
    else:
        response_text = ""
    smart_delta = tail_from_line(smart_log, smart0 + 1)
    nim_delta = tail_from_line(nim_log, nim0 + 1)
    smart_delta_path = prefix.with_suffix(".smart_delta.log")
    nim_delta_path = prefix.with_suffix(".nim_delta.log")
    smart_delta_path.write_text(smart_delta, encoding="utf-8")
    nim_delta_path.write_text(nim_delta, encoding="utf-8")
    timing = {
        "name": name,
        "trace": trace,
        "start_local": start_local,
        "end_local": end_local,
        "elapsed_s": round(elapsed, 3),
        "curl_cmd_redacted": redact_text(" ".join(cmd)),
    }
    prefix.with_suffix(".timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=2), encoding="utf-8")
    return ProbeResult(
        name=name,
        trace=trace,
        start_local=start_local,
        end_local=end_local,
        elapsed_s=elapsed,
        metrics=parse_curl_metrics(result.stdout),
        response_preview=response_text[:1000],
        smart_delta_path=smart_delta_path.name,
        nim_delta_path=nim_delta_path.name,
    )


def compute_curl_max_time(root: Path, floor: int = 240) -> int:
    env = parse_env_file(root / ".env")
    candidates = [floor]
    for key in ("NIM_PROXY_READ_TIMEOUT_SECONDS", "NIM_PROXY_REQUEST_WALL_TIMEOUT_SECONDS"):
        try:
            candidates.append(int(float(env.get(key, "0"))) + 90)
        except ValueError:
            pass
    return max(candidates)


def run_curl_probes(root: Path, output_dir: Path) -> list[ProbeResult]:
    curl_max = compute_curl_max_time(root)
    results: list[ProbeResult] = []
    trace_4010 = f"TRACE-CURL4010-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    results.append(
        curl_probe(
            root,
            output_dir,
            name="curl_4010_nonstream",
            url="http://127.0.0.1:4010/v1/chat/completions",
            payload=make_openai_payload(trace_4010, "z-ai/glm-5.2", stream=False),
            headers=["Authorization: Bearer nim-proxy-local", "Content-Type: application/json"],
            curl_max_time=curl_max,
        )
    )
    snapshot(root, "after_curl_4010", output_dir)
    trace_4000 = f"TRACE-CURL4000-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    results.append(
        curl_probe(
            root,
            output_dir,
            name="curl_4000_nonstream",
            url="http://127.0.0.1:4000/v1/messages",
            payload=make_anthropic_payload(trace_4000),
            headers=["Content-Type: application/json", "x-api-key: sk-forge-local-anytoken"],
            curl_max_time=curl_max,
        )
    )
    snapshot(root, "after_curl_4000", output_dir)
    return results


def poll_status(output_dir: Path, watch_seconds: int, interval: int) -> None:
    samples_path = output_dir / "vscode_watch_samples.jsonl"
    human_path = output_dir / "vscode_watch_samples_human.log"
    deadline = time.time() + watch_seconds
    while time.time() < deadline:
        status = read_json_url("http://127.0.0.1:4000/_forge/status", timeout=10)
        stats = read_json_url("http://127.0.0.1:4010/stats", timeout=10)
        sample = {
            "local_time": local_time(),
            "epoch": now_epoch(),
            "smart": {
                "active_requests": status.get("active_requests"),
                "total_requests": status.get("total_requests"),
                "total_errors": status.get("total_errors"),
                "requests": status.get("requests", []),
                "retry": status.get("retry", {}),
                "context_budget": status.get("context_budget", {}),
            },
            "nim": {
                "request_count": stats.get("request_count"),
                "retry_count": stats.get("retry_count"),
                "fallback_count": stats.get("fallback_count"),
                "settings": stats.get("settings", {}),
                "pool": stats.get("pool", {}),
            },
        }
        with samples_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(sample, ensure_ascii=False) + "\n")
        keys = ((sample["nim"].get("pool") or {}).get("keys") or [])
        key_summary = ",".join(
            f"{key.get('key_id')}:s{key.get('success_count')}/e{key.get('error_count')}/in{key.get('in_flight')}"
            for key in keys
        )
        reqs = sample["smart"].get("requests") or []
        with human_path.open("a", encoding="utf-8") as handle:
            handle.write(
                f"{sample['local_time']} active={sample['smart'].get('active_requests')} "
                f"smart_total={sample['smart'].get('total_requests')} "
                f"smart_errors={sample['smart'].get('total_errors')} "
                f"nim_req={sample['nim'].get('request_count')} "
                f"nim_retry={sample['nim'].get('retry_count')} "
                f"keys=[{key_summary}] active_reqs={json.dumps(reqs, ensure_ascii=False)}\n"
            )
        time.sleep(interval)


def run_vscode_watch(root: Path, output_dir: Path, watch_seconds: int, interval: int) -> dict[str, Any]:
    smart_log = Path("/tmp/forge_smart_proxy.log")
    nim_log = Path("/tmp/forge_nim_proxy.log")
    smart0 = line_count(smart_log)
    nim0 = line_count(nim_log)
    trace = f"TRACE-VSCODE-WATCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    instruction = f"{trace} 请只回答：收到 {trace}"
    (output_dir / "vscode_instruction.txt").write_text(instruction + "\n", encoding="utf-8")
    print("\n============================================================")
    print("请现在在 VS Code Claude Code 里发送下面这句话：\n")
    print(instruction)
    print("\n发送完成后，不要等 VS Code 返回，立刻回到这个终端按 Enter。")
    print(f"脚本会自动观察 {watch_seconds}s，每 {interval}s 采样一次。")
    print("============================================================\n")
    input()
    sent = {"sent_confirm_local": local_time(), "sent_confirm_epoch": now_epoch(), "trace": trace}
    (output_dir / "vscode_sent_timing.json").write_text(json.dumps(sent, ensure_ascii=False, indent=2), encoding="utf-8")
    poll_status(output_dir, watch_seconds=watch_seconds, interval=interval)
    print("\n============================================================")
    print("观察窗口结束。若 VS Code 仍在转圈，请现在手动停止 Claude Code 执行。")
    print("停止后回到这个终端按 Enter；如果已经结束，也直接按 Enter。")
    print("============================================================\n")
    input()
    stopped = {"manual_stop_or_done_local": local_time(), "manual_stop_or_done_epoch": now_epoch(), "trace": trace}
    (output_dir / "vscode_manual_stop_or_done_timing.json").write_text(
        json.dumps(stopped, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    post_stop_seconds = 180
    poll_status(output_dir, watch_seconds=post_stop_seconds, interval=interval)
    smart_delta = tail_from_line(smart_log, smart0 + 1)
    nim_delta = tail_from_line(nim_log, nim0 + 1)
    (output_dir / "vscode_smart_delta.log").write_text(smart_delta, encoding="utf-8")
    (output_dir / "vscode_nim_delta.log").write_text(nim_delta, encoding="utf-8")
    snapshot(root, "after_vscode_watch", output_dir)
    return {
        "trace": trace,
        "instruction": instruction,
        "watch_seconds": watch_seconds,
        "interval": interval,
        "post_stop_seconds": post_stop_seconds,
    }


def load_indexed_nvidia_keys_from_env(root: Path) -> list[tuple[str, str]]:
    env = parse_env_file(root / ".env")
    keys: list[tuple[str, str]] = []
    for index in range(1, 11):
        key = env.get(f"NVIDIA_API_KEY_{index}")
        if key:
            keys.append((f"key-{index}", key))
    return keys


def http_probe(
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes | None,
    timeout: int,
) -> dict[str, Any]:
    started = time.time()
    request = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - diagnostic URL from caller
            raw = response.read()
            status = response.status
            response_headers = dict(response.headers.items())
            error = ""
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
        response_headers = dict(exc.headers.items())
        error = f"HTTPError: {exc}"
    except Exception as exc:
        raw = b""
        status = None
        response_headers = {}
        error = f"{type(exc).__name__}: {exc}"
    elapsed = time.time() - started
    body_text = raw.decode("utf-8", errors="replace")
    return {
        "method": method,
        "url": url,
        "status": status,
        "elapsed_s": round(elapsed, 3),
        "error": redact_text(error),
        "headers": {k: redact_text(v) for k, v in response_headers.items() if k.lower() in {
            "content-type", "retry-after", "x-request-id", "x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset"
        }},
        "body_preview": redact_text(body_text[:12000]),
        "body_bytes": len(raw),
    }


def summarize_models_response(result: dict[str, Any], wanted_model: str) -> dict[str, Any]:
    body = result.get("body_preview") or ""
    out: dict[str, Any] = {"wanted_model": wanted_model, "wanted_present": False, "glm_like_ids": []}
    try:
        data = json.loads(body)
    except Exception:
        return out
    items = data.get("data") if isinstance(data, dict) else None
    ids: list[str] = []
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and item.get("id"):
                ids.append(str(item["id"]))
            elif isinstance(item, str):
                ids.append(item)
    out["wanted_present"] = wanted_model in ids
    out["glm_like_ids"] = [item for item in ids if "glm" in item.lower() or "z-ai" in item.lower()][:50]
    out["model_count"] = len(ids)
    return out


def run_direct_upstream_probes(root: Path, output_dir: Path, *, model: str, timeout: int, key_limit: int | None = None) -> list[dict[str, Any]]:
    keys = load_indexed_nvidia_keys_from_env(root)
    results: list[dict[str, Any]] = []
    if not keys:
        result = {"error": "No NVIDIA_API_KEY_1..10 found in .env"}
        (output_dir / "direct_upstream_probes.json").write_text(json.dumps([result], ensure_ascii=False, indent=2), encoding="utf-8")
        return [result]
    if key_limit is not None and key_limit > 0:
        keys = keys[:key_limit]
    for key_id, api_key in keys:
        auth = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        models_result = http_probe(
            method="GET",
            url="https://integrate.api.nvidia.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            body=None,
            timeout=min(timeout, 60),
        )
        chat_trace = f"TRACE-DIRECT-{key_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        chat_payload = json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": f"{chat_trace} ping，只回答 pong"}],
                "stream": False,
                "max_tokens": 16,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        chat_result = http_probe(
            method="POST",
            url="https://integrate.api.nvidia.com/v1/chat/completions",
            headers=auth,
            body=chat_payload,
            timeout=timeout,
        )
        results.append(
            {
                "key_id": key_id,
                "model": model,
                "models_endpoint": models_result,
                "models_summary": summarize_models_response(models_result, model),
                "chat_trace": chat_trace,
                "chat_completions": chat_result,
            }
        )
    (output_dir / "direct_upstream_probes.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return results


def make_summary(
    root: Path,
    output_dir: Path,
    *,
    profile: str,
    applied_updates: dict[str, str],
    curl_results: list[ProbeResult],
    direct_results: list[dict[str, Any]] | None,
    vscode_result: dict[str, Any] | None,
) -> dict[str, Any]:
    before = json.loads((output_dir / "before_snapshot.json").read_text(encoding="utf-8"))
    final = snapshot(root, "final", output_dir)
    summary = {
        "generated_local": local_time(),
        "generated_epoch": now_epoch(),
        "root": str(root),
        "profile": profile,
        "applied_env_updates": applied_updates,
        "git_head_before": before.get("git_log", "").splitlines()[0] if before.get("git_log") else "",
        "git_head_final": final.get("git_log", "").splitlines()[0] if final.get("git_log") else "",
        "selected_env_final": final.get("selected_env", {}),
        "curl_results": [
            {
                "name": item.name,
                "trace": item.trace,
                "start_local": item.start_local,
                "end_local": item.end_local,
                "elapsed_s": round(item.elapsed_s, 3),
                "metrics": item.metrics,
                "response_preview": item.response_preview,
                "smart_delta_path": item.smart_delta_path,
                "nim_delta_path": item.nim_delta_path,
            }
            for item in curl_results
        ],
        "direct_upstream_probes": direct_results or [],
        "vscode_watch": vscode_result,
        "final_4010_stats": final.get("stats_4010", {}),
        "final_4000_status": final.get("status_4000", {}),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# FORGE NIM Diagnostic Summary",
        "",
        f"- generated_local: `{summary['generated_local']}`",
        f"- profile: `{profile}`",
        f"- git_head_final: `{summary['git_head_final']}`",
        f"- output_dir: `{output_dir}`",
        "",
        "## Applied env updates",
        "",
        "```json",
        json.dumps(applied_updates, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Curl probes",
        "",
    ]
    for item in summary["curl_results"]:
        lines.extend(
            [
                f"### {item['name']}",
                "",
                f"- trace: `{item['trace']}`",
                f"- start: `{item['start_local']}`",
                f"- end: `{item['end_local']}`",
                f"- elapsed_s: `{item['elapsed_s']}`",
                f"- metrics: `{json.dumps(item['metrics'], ensure_ascii=False)}`",
                f"- response_preview: `{item['response_preview'][:300]}`",
                "",
            ]
        )
    if direct_results:
        lines.extend(["## Direct NVIDIA upstream probes", "", "```json", json.dumps(direct_results, ensure_ascii=False, indent=2)[:8000], "```", ""])
    if vscode_result:
        lines.extend(
            [
                "## VS Code watch",
                "",
                f"- trace: `{vscode_result['trace']}`",
                f"- watch_seconds: `{vscode_result['watch_seconds']}`",
                f"- interval: `{vscode_result['interval']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Final stats excerpt",
            "",
            "```json",
            json.dumps(
                {
                    "nim": summary["final_4010_stats"],
                    "smart": {
                        "active_requests": summary["final_4000_status"].get("active_requests"),
                        "total_requests": summary["final_4000_status"].get("total_requests"),
                        "total_errors": summary["final_4000_status"].get("total_errors"),
                        "retry": summary["final_4000_status"].get("retry"),
                        "context_budget": summary["final_4000_status"].get("context_budget"),
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            "```",
            "",
        ]
    )
    (output_dir / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def create_tarball(output_dir: Path) -> Path:
    tar_path = output_dir.with_suffix(".tgz")
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(output_dir, arcname=output_dir.name)
    return tar_path


def push_sanitized_artifact(root: Path, output_dir: Path, branch: str | None = None) -> str:
    timestamp = output_dir.name.replace("forge_nim_diag_", "")
    branch_name = branch or f"diagnostics/forge-nim-{timestamp}"
    worktree = Path("/tmp") / f"forge_diag_push_{timestamp}_{os.getpid()}"
    push_log = output_dir / "push_sanitized_artifact.log"
    if worktree.exists():
        shutil.rmtree(worktree)
    try:
        # A previous failed artifact push can leave a local diagnostics/* branch
        # behind. Delete that local branch before creating the orphan branch
        # again; remote state is handled by the final force-push.
        existing = run_cmd(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"], cwd=root, timeout=30)
        if existing.returncode == 0:
            run_checked_logged(["git", "branch", "-D", branch_name], cwd=root, timeout=120, log_path=push_log)
        run_cmd(["git", "worktree", "prune"], cwd=root, timeout=120)
        run_checked_logged(["git", "worktree", "add", "--detach", str(worktree), "HEAD"], cwd=root, timeout=120, log_path=push_log)
        run_checked_logged(["git", "checkout", "--orphan", branch_name], cwd=worktree, timeout=120, log_path=push_log)
        run_cmd(["git", "rm", "-rf", "."], cwd=worktree, timeout=120)
        dest = worktree / output_dir.name
        shutil.copytree(output_dir, dest)
        # Remove raw backup/path markers if present; redacted env backups are safe.
        for raw_path in list(dest.glob("*.path.txt")) + list(dest.glob("*raw_backup_path.txt")):
            raw_path.unlink()
        run_checked_logged(["git", "add", "-f", "."], cwd=worktree, timeout=120, log_path=push_log)
        run_checked_logged(
            [
                "git",
                "-c",
                "user.name=Arena.ai Agent Mode",
                "-c",
                "user.email=agent@arena.ai",
                "commit",
                "--no-verify",
                "-m",
                f"diagnostics: forge nim trace {timestamp}",
            ],
            cwd=worktree,
            timeout=120,
            log_path=push_log,
        )
        run_checked_logged(["git", "push", "-f", "origin", branch_name], cwd=worktree, timeout=180, log_path=push_log)
    finally:
        run_cmd(["git", "worktree", "remove", "--force", str(worktree)], cwd=root, timeout=120)
    return branch_name


@dataclass(slots=True)
class Args:
    root: Path
    profile: str
    restart: bool
    restart_timeout: int
    restart_mode: str
    truncate_logs: bool
    curl_probes: bool
    direct_upstream_probes: bool
    direct_timeout: int
    direct_model: str
    direct_key_limit: int
    vscode_watch: bool
    watch_seconds: int
    interval: int
    push_sanitized_artifact: bool
    artifact_branch: str | None
    push_existing: Path | None
    output_base: Path


def parse_args(argv: list[str]) -> Args:
    parser = argparse.ArgumentParser(description="Run FORGE Smart Proxy / NIM diagnostics")
    parser.add_argument("--root", default=os.getcwd(), help="FORGE repo root")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="current")
    parser.add_argument("--restart", action="store_true", help="restart 4000/4010 before probes")
    parser.add_argument("--restart-timeout", type=int, default=900)
    parser.add_argument("--restart-mode", choices=["fast", "full"], default="fast", help="fast skips forge-start full local-model self-check")
    parser.add_argument("--truncate-logs", action="store_true", help="truncate /tmp/forge_* logs before restart")
    parser.add_argument("--curl-probes", action="store_true", help="run 4010 and 4000 non-stream curl probes")
    parser.add_argument("--direct-upstream-probes", action="store_true", help="probe NVIDIA /v1/models and /v1/chat/completions directly with indexed keys")
    parser.add_argument("--direct-timeout", type=int, default=90)
    parser.add_argument("--direct-model", default="z-ai/glm-5.2")
    parser.add_argument("--direct-key-limit", type=int, default=0, help="0 means all indexed keys; use 1 for long one-key probes")
    parser.add_argument("--vscode-watch", action="store_true", help="interactive VS Code fixed-window watcher")
    parser.add_argument("--watch-seconds", type=int, default=1500)
    parser.add_argument("--interval", type=int, default=15)
    parser.add_argument("--push-sanitized-artifact", action="store_true", help="push sanitized artifact to a diagnostics/* branch")
    parser.add_argument("--artifact-branch", default=None)
    parser.add_argument("--push-existing", default=None, help="push an existing diagnostic output directory without rerunning probes")
    parser.add_argument("--output-base", default="/tmp")
    ns = parser.parse_args(argv)
    return Args(
        root=Path(ns.root).expanduser().resolve(),
        profile=ns.profile,
        restart=bool(ns.restart),
        restart_timeout=int(ns.restart_timeout),
        restart_mode=str(ns.restart_mode),
        truncate_logs=bool(ns.truncate_logs),
        curl_probes=bool(ns.curl_probes),
        direct_upstream_probes=bool(ns.direct_upstream_probes),
        direct_timeout=int(ns.direct_timeout),
        direct_model=str(ns.direct_model),
        direct_key_limit=int(ns.direct_key_limit),
        vscode_watch=bool(ns.vscode_watch),
        watch_seconds=int(ns.watch_seconds),
        interval=int(ns.interval),
        push_sanitized_artifact=bool(ns.push_sanitized_artifact),
        artifact_branch=ns.artifact_branch,
        push_existing=Path(ns.push_existing).expanduser().resolve() if ns.push_existing else None,
        output_base=Path(ns.output_base).expanduser().resolve(),
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not args.root.exists():
        print(f"Root not found: {args.root}", file=sys.stderr)
        return 2
    if args.push_existing is not None:
        existing = args.push_existing
        if not existing.exists() or not existing.is_dir():
            print(f"Existing diagnostic directory not found: {existing}", file=sys.stderr)
            return 2
        tarball = create_tarball(existing)
        pushed_branch = ""
        push_failed = ""
        if args.push_sanitized_artifact:
            try:
                pushed_branch = push_sanitized_artifact(args.root, existing, branch=args.artifact_branch)
                (existing / "PUSHED_BRANCH.txt").write_text(pushed_branch + "\n", encoding="utf-8")
            except Exception as exc:  # keep the already collected artifact usable
                push_failed = f"{type(exc).__name__}: {exc}"
                (existing / "PUSH_FAILED.txt").write_text(push_failed + "\n", encoding="utf-8")
        print("\nDONE")
        print(f"DIAG_OUTPUT_DIR={existing}")
        print(f"DIAG_TARBALL={tarball}")
        if pushed_branch:
            print(f"PUSHED_BRANCH={pushed_branch}")
        if push_failed:
            print(f"PUSH_FAILED={push_failed}")
            print(f"PUSH_LOG={existing / 'push_sanitized_artifact.log'}")
        return 0
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output_base / f"forge_nim_diag_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=False)

    print(f"DIAG_OUTPUT_DIR={output_dir}")
    print(f"PROFILE={args.profile}")
    print(f"ROOT={args.root}")

    applied_updates = apply_profile(args.root, args.profile, output_dir)
    if applied_updates:
        print("APPLIED_ENV_UPDATES=" + json.dumps(applied_updates, ensure_ascii=False, sort_keys=True))

    if args.truncate_logs and not args.restart:
        truncate_logs()

    if args.restart:
        if args.restart_mode == "full":
            print("Restarting 4000/4010 via scripts/forge-start.sh full self-check ...")
        else:
            print("Fast restarting only NIM sidecar 4010 and Smart Proxy 4000 (skips forge-start full model self-check) ...")
        restart_services(args.root, output_dir, timeout=args.restart_timeout, mode=args.restart_mode)

    snapshot(args.root, "before", output_dir)
    curl_results: list[ProbeResult] = []
    if args.curl_probes:
        print("Running curl probes: 4010 non-stream, then 4000 non-stream ...")
        curl_results = run_curl_probes(args.root, output_dir)

    direct_results = None
    if args.direct_upstream_probes:
        print("Running direct NVIDIA upstream probes: /v1/models and /v1/chat/completions ...")
        direct_results = run_direct_upstream_probes(
            args.root,
            output_dir,
            model=args.direct_model,
            timeout=args.direct_timeout,
            key_limit=args.direct_key_limit or None,
        )

    vscode_result = None
    if args.vscode_watch:
        vscode_result = run_vscode_watch(args.root, output_dir, args.watch_seconds, args.interval)

    summary = make_summary(
        args.root,
        output_dir,
        profile=args.profile,
        applied_updates=applied_updates,
        curl_results=curl_results,
        direct_results=direct_results,
        vscode_result=vscode_result,
    )
    tarball = create_tarball(output_dir)
    pushed_branch = ""
    push_failed = ""
    if args.push_sanitized_artifact:
        try:
            pushed_branch = push_sanitized_artifact(args.root, output_dir, branch=args.artifact_branch)
            (output_dir / "PUSHED_BRANCH.txt").write_text(pushed_branch + "\n", encoding="utf-8")
        except Exception as exc:  # keep diagnostics usable even if artifact push fails
            push_failed = f"{type(exc).__name__}: {exc}"
            (output_dir / "PUSH_FAILED.txt").write_text(push_failed + "\n", encoding="utf-8")

    print("\nDONE")
    print(f"DIAG_OUTPUT_DIR={output_dir}")
    print(f"DIAG_TARBALL={tarball}")
    print(f"SUMMARY_JSON={output_dir / 'summary.json'}")
    print(f"SUMMARY_MD={output_dir / 'SUMMARY.md'}")
    if pushed_branch:
        print(f"PUSHED_BRANCH={pushed_branch}")
    if push_failed:
        print(f"PUSH_FAILED={push_failed}")
        print(f"PUSH_LOG={output_dir / 'push_sanitized_artifact.log'}")
    # Keep a compact one-line result for copy/paste if branch push is disabled.
    print(
        "CURL_RESULTS="
        + json.dumps(
            [
                {"name": item["name"], "metrics": item["metrics"], "elapsed_s": item["elapsed_s"]}
                for item in summary.get("curl_results", [])
            ],
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

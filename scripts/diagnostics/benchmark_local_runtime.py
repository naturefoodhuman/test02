#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-26 00:00:00

"""
One-click local runtime benchmark for MTPLX / Claude Code proxy.

What it does by default:
- Temporarily edits config/model_runtime.yaml for several 8080 Qwen profiles.
- Restarts local FORGE services through scripts/stop_local_models.sh + scripts/forge-start.sh.
- Sends fixed prompts through the Anthropic-compatible Smart Proxy (4000).
- Copies /tmp/mtplx_8080.log for each profile.
- Parses mtplx_openai_generation metrics.
- Runs local streaming diagnostics per profile.
- Restores the original config/model_runtime.yaml at the end.
- Writes all artifacts under diagnostics/local_runtime_benchmark/<timestamp>/.

Designed for the user to run once and send the generated directory/report back
for analysis.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "model_runtime.yaml"
OUT_ROOT = ROOT / "diagnostics" / "local_runtime_benchmark"
MTPLX_LOG = Path("/tmp/mtplx_8080.log")
SMART_PROXY_LOG = Path("/tmp/forge_smart_proxy.log")
LITELLM_LOG = Path("/tmp/forge_litellm_4001.log")

PROMPTS = {
    "short_pong": "只回复 pong",
    "medium_state_machine": "用中文用三段话解释什么是状态机。",
    "agentic_summary": (
        "你是 FORGE Factory Orchestrator。请用中文输出 5 条接手规则，"
        "每条不超过 25 字。不要写代码，不要展开长篇解释。"
    ),
}

PROFILE_ARGS = {
    "mtp_depth3": [
        "--profile", "sustained", "--mtp", "--depth", "3",
        "--stream-interval", "1", "--reasoning", "off", "--max-tokens", "512",
    ],
    "no_mtp": [
        "--profile", "sustained", "--no-mtp",
        "--reasoning", "off", "--max-tokens", "512",
    ],
    "mtp_depth3_kv_q8": [
        "--profile", "sustained", "--mtp", "--depth", "3",
        "--stream-interval", "1", "--reasoning", "off", "--max-tokens", "512",
        "--paged-kv-quantization", "q8",
    ],
    "mtp_depth3_kv_q4": [
        "--profile", "sustained", "--mtp", "--depth", "3",
        "--stream-interval", "1", "--reasoning", "off", "--max-tokens", "512",
        "--paged-kv-quantization", "q4",
    ],
}


def run_cmd(cmd: list[str], cwd: Path = ROOT, timeout: int | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "elapsed_s": time.perf_counter() - t0,
            "output": proc.stdout,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "returncode": 124,
            "elapsed_s": time.perf_counter() - t0,
            "output": (exc.stdout or "") + f"\nTIMEOUT after {timeout}s",
        }


def load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}


def save_config(cfg: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")


def set_8080_extra_args(args: list[str]) -> None:
    cfg = load_config()
    servers = cfg.setdefault("servers", {})
    server = servers.get(8080) or servers.get("8080")
    if server is None:
        raise RuntimeError("config/model_runtime.yaml missing servers.8080")
    server["extra_args"] = args
    save_config(cfg)


def parse_generation_events(log_path: Path) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []
    rows = []
    for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line.startswith("{") or "mtplx_openai_generation" not in line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows


def copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def truncate_logs() -> None:
    for p in [MTPLX_LOG, SMART_PROXY_LOG, LITELLM_LOG]:
        try:
            p.write_text("", encoding="utf-8")
        except Exception:
            pass


def call_proxy(prompt: str, model: str, max_tokens: int, stream: bool, timeout: float) -> dict[str, Any]:
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "stream": stream,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "content-type": "application/json",
        "x-api-key": "sk-forge-local-anytoken",
        "anthropic-version": "2023-06-01",
    }
    t0 = time.perf_counter()
    out: dict[str, Any] = {
        "prompt": prompt,
        "model": model,
        "max_tokens": max_tokens,
        "stream": stream,
    }
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout, read=timeout)) as client:
            if not stream:
                resp = client.post("http://127.0.0.1:4000/v1/messages", headers=headers, json=payload)
                out["http_status"] = resp.status_code
                out["elapsed_s"] = time.perf_counter() - t0
                out["raw_text"] = resp.text[:4000]
                try:
                    data = resp.json()
                    content = data.get("content", [])
                    text = "".join(block.get("text", "") for block in content if isinstance(block, dict))
                    out["text_preview"] = text[:500]
                    out["text_len"] = len(text)
                except Exception as exc:
                    out["json_error"] = repr(exc)
                return out

            first_delta = None
            delta_count = 0
            text_parts: list[str] = []
            with client.stream("POST", "http://127.0.0.1:4000/v1/messages", headers=headers, json=payload) as resp:
                out["http_status"] = resp.status_code
                current_event = ""
                for line in resp.iter_lines():
                    if not line:
                        current_event = ""
                        continue
                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip()
                        continue
                    if line.startswith("data:") and current_event == "content_block_delta":
                        raw = line.split(":", 1)[1].strip()
                        try:
                            data = json.loads(raw)
                        except Exception:
                            continue
                        text = (data.get("delta") or {}).get("text")
                        if text:
                            if first_delta is None:
                                first_delta = time.perf_counter() - t0
                            delta_count += 1
                            text_parts.append(str(text))
            out["elapsed_s"] = time.perf_counter() - t0
            out["first_delta_s"] = first_delta
            out["delta_count"] = delta_count
            out["text_preview"] = "".join(text_parts)[:500]
            out["text_len"] = len("".join(text_parts))
            return out
    except Exception as exc:
        out["elapsed_s"] = time.perf_counter() - t0
        out["exception"] = repr(exc)
        return out


def summarize_report(results: dict[str, Any]) -> str:
    lines = [
        "# Local Runtime Benchmark Report",
        "",
        f"Generated: {results['generated_at']}",
        "",
        "## Summary Table",
        "",
        "| profile | prompt | stream | client_s | first_delta_s | prompt_tokens | completion_tokens | mtplx_elapsed_s | tok_s | e2e_tok_s |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for profile in results["profiles"]:
        for run in profile.get("runs", []):
            metric = run.get("mtplx_metric") or {}
            lines.append(
                "| {profile} | {prompt} | {stream} | {client:.2f} | {first} | {pt} | {ct} | {me:.2f} | {tok:.2f} | {e2e:.2f} |".format(
                    profile=profile["name"],
                    prompt=run["prompt_name"],
                    stream=str(run["request"].get("stream")),
                    client=float(run["request"].get("elapsed_s", 0) or 0),
                    first="-" if run["request"].get("first_delta_s") is None else f"{float(run['request'].get('first_delta_s')):.2f}",
                    pt=metric.get("prompt_tokens", ""),
                    ct=metric.get("completion_tokens", ""),
                    me=float(metric.get("elapsed_s", 0) or 0),
                    tok=float(metric.get("tok_s", 0) or 0),
                    e2e=float(metric.get("end_to_end_tok_s", 0) or 0),
                )
            )
    lines.extend(
        [
            "",
            "## Interpretation Notes",
            "",
            "- Compare rows only when prompt and completion length are similar.",
            "- Short prompts may favor no-MTP because draft/verify overhead can dominate.",
            "- MTP benefits should be judged on repeated medium/long generations and stable token counts.",
            "- Streaming first_delta includes on-demand model startup if 8080 was not already loaded.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", default="mtp_depth3,no_mtp,mtp_depth3_kv_q8,mtp_depth3_kv_q4")
    parser.add_argument("--prompts", default="short_pong,medium_state_machine,agentic_summary")
    parser.add_argument("--model", default="claude-opus-4-8-1m")
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--timeout", type=float, default=420.0)
    parser.add_argument("--skip-stream", action="store_true", help="Skip stream=true requests")
    parser.add_argument("--keep-running", action="store_true", help="Do not stop local models at the end")
    args = parser.parse_args()

    selected_profiles = [p.strip() for p in args.profiles.split(",") if p.strip()]
    selected_prompts = [p.strip() for p in args.prompts.split(",") if p.strip()]
    for p_name in selected_profiles:
        if p_name not in PROFILE_ARGS:
            raise SystemExit(f"Unknown profile {p_name}; choices={list(PROFILE_ARGS)}")
    for prompt_name in selected_prompts:
        if prompt_name not in PROMPTS:
            raise SystemExit(f"Unknown prompt {prompt_name}; choices={list(PROMPTS)}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = OUT_ROOT / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    original_config = CONFIG_PATH.read_text(encoding="utf-8")
    (out_dir / "model_runtime.original.yaml").write_text(original_config, encoding="utf-8")

    results: dict[str, Any] = {
        "generated_at": ts,
        "profiles": [],
        "args": vars(args),
    }

    try:
        for profile_name in selected_profiles:
            profile_dir = out_dir / profile_name
            profile_dir.mkdir(parents=True, exist_ok=True)
            print(f"\n=== Profile: {profile_name} ===", flush=True)
            set_8080_extra_args(PROFILE_ARGS[profile_name])
            (profile_dir / "model_runtime.yaml").write_text(CONFIG_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            truncate_logs()

            stop_res = run_cmd(["bash", "scripts/stop_local_models.sh"], timeout=120)
            (profile_dir / "stop.log").write_text(stop_res["output"], encoding="utf-8")
            start_res = run_cmd(["bash", "scripts/forge-start.sh"], timeout=900)
            (profile_dir / "forge_start.log").write_text(start_res["output"], encoding="utf-8")

            profile_result: dict[str, Any] = {
                "name": profile_name,
                "extra_args": PROFILE_ARGS[profile_name],
                "start_returncode": start_res["returncode"],
                "runs": [],
            }

            for prompt_name in selected_prompts:
                print(f"Running {profile_name}/{prompt_name} non-stream", flush=True)
                before = len(parse_generation_events(MTPLX_LOG))
                req = call_proxy(PROMPTS[prompt_name], args.model, args.max_tokens, False, args.timeout)
                events = parse_generation_events(MTPLX_LOG)
                metric = events[-1] if len(events) > before else (events[-1] if events else None)
                profile_result["runs"].append({
                    "prompt_name": prompt_name,
                    "request": req,
                    "mtplx_metric": metric,
                })
                (profile_dir / f"{prompt_name}.response.json").write_text(json.dumps(req, indent=2, ensure_ascii=False), encoding="utf-8")

                if not args.skip_stream:
                    print(f"Running {profile_name}/{prompt_name} stream", flush=True)
                    before = len(parse_generation_events(MTPLX_LOG))
                    req_s = call_proxy(PROMPTS[prompt_name], args.model, min(args.max_tokens, 256), True, args.timeout)
                    events = parse_generation_events(MTPLX_LOG)
                    metric_s = events[-1] if len(events) > before else (events[-1] if events else None)
                    profile_result["runs"].append({
                        "prompt_name": prompt_name + "_stream",
                        "request": req_s,
                        "mtplx_metric": metric_s,
                    })
                    (profile_dir / f"{prompt_name}.stream.response.json").write_text(json.dumps(req_s, indent=2, ensure_ascii=False), encoding="utf-8")

            copy_if_exists(MTPLX_LOG, profile_dir / "mtplx_8080.log")
            copy_if_exists(SMART_PROXY_LOG, profile_dir / "forge_smart_proxy.log")
            copy_if_exists(LITELLM_LOG, profile_dir / "forge_litellm_4001.log")

            mtp_diag = run_cmd(["python3", "scripts/diagnostics/test_mtp_effectiveness.py"], timeout=120)
            (profile_dir / "test_mtp_effectiveness.txt").write_text(mtp_diag["output"], encoding="utf-8")
            stream_diag = run_cmd(["python3", "scripts/diagnostics/test_local_streaming.py"], timeout=300)
            (profile_dir / "test_local_streaming.txt").write_text(stream_diag["output"], encoding="utf-8")

            results["profiles"].append(profile_result)
    finally:
        CONFIG_PATH.write_text(original_config, encoding="utf-8")
        if not args.keep_running:
            run_cmd(["bash", "scripts/stop_local_models.sh"], timeout=120)

    (out_dir / "report.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "report.md").write_text(summarize_report(results), encoding="utf-8")
    print(f"\nDONE: {out_dir}")
    print(f"Main report: {out_dir / 'report.md'}")
    print("Send the whole directory or report.json/report.md plus logs for analysis.")


if __name__ == "__main__":
    main()

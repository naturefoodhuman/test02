#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-26 00:00:00

"""
One-click local runtime benchmark for MTPLX / Claude Code proxy.

Final benchmark design goals:
- Strict profile control: each run differs only by 8080 extra_args profile.
- Controlled prompts: one medium controlled output, one long-context controlled output.
- Repeats + seed: reduce single-run noise and record seed per request.
- Artifacts: report.json, report.md, copied logs, per-profile diagnostics.
- Safety: restore config/model_runtime.yaml and stop local models at the end.

Default final run:
  python3 scripts/diagnostics/benchmark_local_runtime.py

Fast smoke run:
  python3 scripts/diagnostics/benchmark_local_runtime.py \
    --profiles mtp_depth3,no_mtp --prompts controlled_medium --repeat 1
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import socket
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


def build_long_context() -> str:
    sections = []
    for i in range(1, 49):
        sections.append(
            f"[记录{i:02d}] FORGE 工厂第{i:02d}项观察："
            f"阶段={'DISCOVERY' if i % 5 == 1 else 'SPEC' if i % 5 == 2 else 'BUILD' if i % 5 == 3 else 'HARDEN' if i % 5 == 4 else 'RETRO'}；"
            f"能力={'联网搜索' if i % 4 == 0 else '隐私网关' if i % 4 == 1 else '文档治理' if i % 4 == 2 else '本地模型'}；"
            f"风险={'高' if i % 7 == 0 else '中' if i % 3 == 0 else '低'}；"
            f"处理建议：保持任务小步、记录证据、运行测试、同步 DEV_LOG 与 CHANGELOG。"
        )
    return "\n".join(sections)


PROMPTS = {
    "controlled_medium": (
        "请严格按以下格式输出，不要添加标题、前言或结尾：\n"
        "- 共 12 行。\n"
        "- 每行以 01 到 12 的两位编号开头。\n"
        "- 每行解释一个状态机概念。\n"
        "- 每行 18 到 30 个中文字符。\n"
        "主题：什么是状态机，以及它为什么适合描述工作流。"
    ),
    "controlled_long_context": (
        "下面是一个项目运行观察清单。请只基于这些记录做摘要。\n\n"
        f"{build_long_context()}\n\n"
        "输出要求：\n"
        "1. 先输出 8 条编号摘要，编号 A1 到 A8，每条不超过 35 个中文字符。\n"
        "2. 再输出 3 条风险，编号 R1 到 R3，每条不超过 35 个中文字符。\n"
        "3. 最后输出 2 条行动建议，编号 N1 到 N2，每条不超过 35 个中文字符。\n"
        "4. 不要输出记录原文，不要输出额外解释。"
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
        return {"cmd": cmd, "returncode": proc.returncode, "elapsed_s": time.perf_counter() - t0, "output": proc.stdout}
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="ignore")
        return {"cmd": cmd, "returncode": 124, "elapsed_s": time.perf_counter() - t0, "output": stdout + f"\nTIMEOUT after {timeout}s"}


def is_listening(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def wait_port(port: int, timeout_s: float) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if is_listening(port):
            return True
        time.sleep(1)
    return False


def shlex_quote(value: str) -> str:
    import shlex
    return shlex.quote(value)


def start_gateway_only(profile_dir: Path, timeout_s: int = 180) -> dict[str, Any]:
    result: dict[str, Any] = {"mode": "proxy-only", "steps": []}
    LITELLM_LOG.write_text("", encoding="utf-8")
    SMART_PROXY_LOG.write_text("", encoding="utf-8")
    litellm_cmd = "bash _infra/start-litellm.sh 4001 > /tmp/forge_litellm_4001.log 2>&1 &"
    smart_cmd = f"{shlex_quote(sys.executable)} _infra/smart_proxy.py > /tmp/forge_smart_proxy.log 2>&1 &"
    subprocess.Popen(litellm_cmd, cwd=str(ROOT), shell=True, executable="/bin/bash")
    ok_4001 = wait_port(4001, timeout_s)
    result["steps"].append({"service": "litellm", "port": 4001, "ready": ok_4001})
    if not ok_4001:
        result["error"] = "LiteLLM 4001 did not become ready"
        return result
    subprocess.Popen(smart_cmd, cwd=str(ROOT), shell=True, executable="/bin/bash")
    ok_4000 = wait_port(4000, 60)
    result["steps"].append({"service": "smart_proxy", "port": 4000, "ready": ok_4000})
    if not ok_4000:
        result["error"] = "Smart Proxy 4000 did not become ready"
    return result


def load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}


def save_config(cfg: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")


def set_8080_extra_args(args: list[str]) -> None:
    cfg = load_config()
    server = (cfg.setdefault("servers", {}).get(8080) or cfg.setdefault("servers", {}).get("8080"))
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


def call_proxy(prompt: str, model: str, max_tokens: int, stream: bool, timeout: float, seed: int) -> dict[str, Any]:
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "stream": stream,
        "seed": seed,
        "temperature": 0.0,
        "top_p": 1.0,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {"content-type": "application/json", "x-api-key": "sk-forge-local-anytoken", "anthropic-version": "2023-06-01"}
    t0 = time.perf_counter()
    out: dict[str, Any] = {"prompt": prompt, "model": model, "max_tokens": max_tokens, "stream": stream, "seed": seed}
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout, read=timeout)) as client:
            if not stream:
                resp = client.post("http://127.0.0.1:4000/v1/messages", headers=headers, json=payload)
                out.update({"http_status": resp.status_code, "elapsed_s": time.perf_counter() - t0, "raw_text": resp.text[:4000]})
                try:
                    data = resp.json()
                    text = "".join(block.get("text", "") for block in data.get("content", []) if isinstance(block, dict))
                    out.update({"text_preview": text[:500], "text_len": len(text)})
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
                        try:
                            data = json.loads(line.split(":", 1)[1].strip())
                        except Exception:
                            continue
                        text = (data.get("delta") or {}).get("text")
                        if text:
                            if first_delta is None:
                                first_delta = time.perf_counter() - t0
                            delta_count += 1
                            text_parts.append(str(text))
            text = "".join(text_parts)
            out.update({"elapsed_s": time.perf_counter() - t0, "first_delta_s": first_delta, "delta_count": delta_count, "text_preview": text[:500], "text_len": len(text)})
            return out
    except Exception as exc:
        out.update({"elapsed_s": time.perf_counter() - t0, "exception": repr(exc)})
        return out


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def build_aggregates(results: dict[str, Any]) -> dict[str, Any]:
    aggregates: dict[str, Any] = {}
    for profile in results["profiles"]:
        p_name = profile["name"]
        aggregates[p_name] = {}
        grouped: dict[str, list[dict[str, Any]]] = {}
        for run in profile.get("runs", []):
            if run["request"].get("stream"):
                continue
            grouped.setdefault(run["prompt_name"], []).append(run)
        for prompt, runs in grouped.items():
            metrics = [r.get("mtplx_metric") or {} for r in runs]
            aggregates[p_name][prompt] = {
                "n": len(runs),
                "client_s_mean": mean([float(r["request"].get("elapsed_s", 0) or 0) for r in runs]),
                "client_s_std": stdev([float(r["request"].get("elapsed_s", 0) or 0) for r in runs]),
                "completion_tokens_mean": mean([float(m.get("completion_tokens", 0) or 0) for m in metrics]),
                "mtplx_elapsed_s_mean": mean([float(m.get("elapsed_s", 0) or 0) for m in metrics]),
                "tok_s_mean": mean([float(m.get("tok_s", 0) or 0) for m in metrics]),
                "e2e_tok_s_mean": mean([float(m.get("end_to_end_tok_s", 0) or 0) for m in metrics]),
            }
    return aggregates


def summarize_report(results: dict[str, Any]) -> str:
    aggregates = build_aggregates(results)
    lines = [
        "# Local Runtime Benchmark Report",
        "",
        f"Generated: {results['generated_at']}",
        "",
        "## Raw Runs",
        "",
        "| profile | prompt | repeat | stream | client_s | first_delta_s | prompt_tokens | completion_tokens | mtplx_elapsed_s | tok_s | e2e_tok_s |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for profile in results["profiles"]:
        for run in profile.get("runs", []):
            metric = run.get("mtplx_metric") or {}
            req = run["request"]
            lines.append(
                "| {profile} | {prompt} | {repeat} | {stream} | {client:.2f} | {first} | {pt} | {ct} | {me:.2f} | {tok:.2f} | {e2e:.2f} |".format(
                    profile=profile["name"], prompt=run["prompt_name"], repeat=run.get("repeat", ""), stream=str(req.get("stream")),
                    client=float(req.get("elapsed_s", 0) or 0), first="-" if req.get("first_delta_s") is None else f"{float(req.get('first_delta_s')):.2f}",
                    pt=metric.get("prompt_tokens", ""), ct=metric.get("completion_tokens", ""), me=float(metric.get("elapsed_s", 0) or 0),
                    tok=float(metric.get("tok_s", 0) or 0), e2e=float(metric.get("end_to_end_tok_s", 0) or 0),
                )
            )
    lines.extend(["", "## Aggregates", "", "| profile | prompt | n | client_s_mean | client_s_std | completion_mean | mtplx_elapsed_mean | tok_s_mean | e2e_tok_s_mean |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"])
    for p_name, prompts in aggregates.items():
        for prompt, a in prompts.items():
            lines.append(f"| {p_name} | {prompt} | {a['n']} | {a['client_s_mean']:.2f} | {a['client_s_std']:.2f} | {a['completion_tokens_mean']:.1f} | {a['mtplx_elapsed_s_mean']:.2f} | {a['tok_s_mean']:.2f} | {a['e2e_tok_s_mean']:.2f} |")
    lines.extend(["", "## Interpretation Notes", "", "- Compare profiles within the same prompt and repeat set.", "- Completion length still matters; prefer aggregate e2e_tok_s and mtplx_elapsed together.", "- If q4/q8 quality differs, do not choose solely by speed.", "- Streaming diagnostics are saved per profile in test_local_streaming.txt.", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", default="mtp_depth3,no_mtp,mtp_depth3_kv_q8,mtp_depth3_kv_q4")
    parser.add_argument("--prompts", default="controlled_medium,controlled_long_context")
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--seed", type=int, default=424242)
    parser.add_argument("--model", default="claude-opus-4-8-1m")
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--startup-mode", choices=["proxy-only", "full"], default="proxy-only")
    parser.add_argument("--include-stream", dest="skip_stream", action="store_false", help="Also run stream=true benchmark requests")
    parser.add_argument("--skip-stream", action="store_true", default=True, help="Skip stream=true benchmark requests (default)")
    parser.add_argument("--keep-running", action="store_true")
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
    results: dict[str, Any] = {"generated_at": ts, "profiles": [], "args": vars(args)}

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
            if args.startup_mode == "full":
                start_res = run_cmd(["bash", "scripts/forge-start.sh"], timeout=900)
                (profile_dir / "forge_start.log").write_text(start_res["output"], encoding="utf-8")
                startup_info = {"mode": "full", "returncode": start_res["returncode"], "elapsed_s": start_res["elapsed_s"]}
            else:
                startup_info = start_gateway_only(profile_dir)
                (profile_dir / "gateway_start.json").write_text(json.dumps(startup_info, indent=2, ensure_ascii=False), encoding="utf-8")
            profile_result: dict[str, Any] = {"name": profile_name, "extra_args": PROFILE_ARGS[profile_name], "startup": startup_info, "runs": []}

            for prompt_name in selected_prompts:
                for repeat_idx in range(1, args.repeat + 1):
                    seed = args.seed + repeat_idx
                    print(f"Running {profile_name}/{prompt_name} repeat={repeat_idx} non-stream", flush=True)
                    before = len(parse_generation_events(MTPLX_LOG))
                    req = call_proxy(PROMPTS[prompt_name], args.model, args.max_tokens, False, args.timeout, seed)
                    events = parse_generation_events(MTPLX_LOG)
                    metric = events[-1] if len(events) > before else (events[-1] if events else None)
                    profile_result["runs"].append({"prompt_name": prompt_name, "repeat": repeat_idx, "request": req, "mtplx_metric": metric})
                    (profile_dir / f"{prompt_name}.r{repeat_idx}.response.json").write_text(json.dumps(req, indent=2, ensure_ascii=False), encoding="utf-8")

                    if not args.skip_stream:
                        print(f"Running {profile_name}/{prompt_name} repeat={repeat_idx} stream", flush=True)
                        before = len(parse_generation_events(MTPLX_LOG))
                        req_s = call_proxy(PROMPTS[prompt_name], args.model, min(args.max_tokens, 256), True, args.timeout, seed)
                        events = parse_generation_events(MTPLX_LOG)
                        metric_s = events[-1] if len(events) > before else (events[-1] if events else None)
                        profile_result["runs"].append({"prompt_name": prompt_name + "_stream", "repeat": repeat_idx, "request": req_s, "mtplx_metric": metric_s})
                        (profile_dir / f"{prompt_name}.r{repeat_idx}.stream.response.json").write_text(json.dumps(req_s, indent=2, ensure_ascii=False), encoding="utf-8")

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

    results["aggregates"] = build_aggregates(results)
    (out_dir / "report.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "report.md").write_text(summarize_report(results), encoding="utf-8")
    print(f"\nDONE: {out_dir}")
    print(f"Main report: {out_dir / 'report.md'}")
    print("Send the whole directory or report.json/report.md plus logs for analysis.")


if __name__ == "__main__":
    main()

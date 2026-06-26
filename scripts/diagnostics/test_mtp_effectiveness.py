#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-26 00:00:00

"""Inspect local MTP / speculative-decoding configuration and logs.

This script does not prove quality. It answers operational questions:
- Does the configured startup command enable MTP/speculative flags?
- Do runtime logs show MTP / draft / acceptance / speedup signals?
- Which model card claims should be checked manually?

Run:
  python3 scripts/diagnostics/test_mtp_effectiveness.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _infra.model_runtime import build_command, get_server_config, load_runtime_config
KEYWORDS = re.compile(r"mtp|multi-token|spec|draft|accept|acceptance|speedup|tok/s|tps", re.IGNORECASE)


def scan_log(path: str) -> list[str]:
    p = Path(path)
    if not p.exists():
        return [f"log not found: {path}"]
    hits = []
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines()[-400:]:
        if KEYWORDS.search(line):
            hits.append(line[-240:])
    return hits or ["no MTP/speculative keywords found in recent log"]


def main() -> None:
    cfg = load_runtime_config()
    print("# MTP / Speculative Decoding Effectiveness Inspection")
    print()
    for raw_port, server in cfg.get("servers", {}).items():
        port = int(raw_port)
        scfg = get_server_config(port)
        print(f"## {port} {scfg.get('name')} ({scfg.get('kind')})")
        print(f"role: {scfg.get('role')}")
        print(f"source: {scfg.get('source')}")
        print("command:")
        print(build_command(port))
        command = build_command(port)
        flags = []
        command_l = command.lower()
        explicit_spec = "--spec-type" in command_l or "--draft" in command_l or "--draft-mtp" in command_l or "--mtp" in command_l
        if explicit_spec:
            flags.append("MTP/speculative flag present in command")
        else:
            flags.append("No explicit MTP/speculative flag in command; runtime may infer from model artifact")
        if scfg.get("kind") == "mtplx":
            flags.append("MTPLX model cards may expose MTP via artifact metadata; verify logs/benchmarks")
        if scfg.get("kind") == "llama_cpp":
            flags.append("llama.cpp path should include --spec-type draft-mtp and --spec-draft-n-max")
        print("signals:")
        for flag in flags:
            print(f"- {flag}")
        print("recent log evidence:")
        for hit in scan_log(str(scfg.get("log_file", "")))[:20]:
            print(f"- {hit}")
        print()
    print("## Ollama runtime env")
    for k, v in (cfg.get("ollama", {}).get("env", {}) or {}).items():
        print(f"- {k}={v}")
    print()
    print("## How to prove MTP speedup")
    print("1. Run a fixed prompt with MTP/spec flags enabled; capture tok/s and acceptance/draft log lines.")
    print("2. Run the same prompt with MTP/spec flags disabled; capture tok/s.")
    print("3. Compare time-to-first-token, decode tok/s, total tokens/sec, and acceptance rate.")
    print("4. For llama.cpp MTP, verify --spec-type draft-mtp and --spec-draft-n-max are present.")


if __name__ == "__main__":
    main()

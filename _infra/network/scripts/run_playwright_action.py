#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 16:05:00

"""Restricted Playwright action CLI wrapper (E7-C6-S1-T1).

Allowed actions:
- open --url URL
- snapshot
- click --ref REF
- type --ref REF --text TEXT
- wait --ms N
- close

The wrapper validates arguments, refuses dangerous cookie/storage/PII/secret
payloads through ArgumentValidator, and never invokes a shell. In real runtime it
executes a local pinned runner (default: mcp-servers/playwright-public/cli.js)
with node. Unit tests use --dry-run.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _infra.network.mcp_guard.argument_validator import ArgumentValidator
from _infra.network.mcp_guard.models import MCPToolCall

ALLOWED_ACTIONS = {"open", "snapshot", "click", "type", "wait", "close"}
DEFAULT_RUNNER = "mcp-servers/playwright-public/cli.js"


def _build_payload(args: argparse.Namespace) -> dict[str, Any]:
    action = args.action
    if action == "open":
        if not args.url:
            raise ValueError("open requires --url")
        return {"url": args.url}
    if action == "snapshot":
        return {}
    if action == "click":
        if not args.ref:
            raise ValueError("click requires --ref")
        return {"ref": args.ref}
    if action == "type":
        if not args.ref or args.text is None:
            raise ValueError("type requires --ref and --text")
        return {"ref": args.ref, "text": args.text}
    if action == "wait":
        if args.ms is None:
            raise ValueError("wait requires --ms")
        if args.ms < 0 or args.ms > 60_000:
            raise ValueError("wait --ms must be between 0 and 60000")
        return {"ms": args.ms}
    if action == "close":
        return {}
    raise ValueError(f"unsupported action: {action}")


def _validate_payload(action: str, payload: dict[str, Any]) -> None:
    result = ArgumentValidator(max_arg_length=4000).validate(
        MCPToolCall(server_id="playwright-public", tool_name=action, args=payload, mode="research")
    )
    if not result.allowed:
        raise ValueError(f"unsafe arguments: {result.reason}")


def _build_argv(action: str, payload: dict[str, Any], runner: str) -> list[str]:
    argv = ["node", runner, action]
    if action == "open":
        argv.extend(["--url", str(payload["url"])])
    elif action == "click":
        argv.extend(["--ref", str(payload["ref"])])
    elif action == "type":
        argv.extend(["--ref", str(payload["ref"]), "--text", str(payload["text"])])
    elif action == "wait":
        argv.extend(["--ms", str(payload["ms"])])
    return argv


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Restricted Playwright action wrapper")
    parser.add_argument("action", choices=sorted(ALLOWED_ACTIONS))
    parser.add_argument("--url")
    parser.add_argument("--ref")
    parser.add_argument("--text")
    parser.add_argument("--ms", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--runner", default=os.getenv("PLAYWRIGHT_ACTION_RUNNER", DEFAULT_RUNNER))
    args = parser.parse_args(argv)

    try:
        payload = _build_payload(args)
        _validate_payload(args.action, payload)
        cmd = _build_argv(args.action, payload, args.runner)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    plan = {"ok": True, "action": args.action, "payload": payload, "argv": cmd}
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, sort_keys=True))
        return 0

    runner_path = Path(args.runner)
    if not runner_path.exists():
        print(json.dumps({"ok": False, "error": f"runner not found: {args.runner}", "plan": plan}, ensure_ascii=False), file=sys.stderr)
        return 3

    proc = subprocess.run(cmd, text=True, check=False)
    return proc.returncode


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

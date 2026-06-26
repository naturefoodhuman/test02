# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-26 00:00:00

"""Local model runtime configuration helper.

Single source for local model startup commands used by:
- scripts/forge-start.sh
- _factory/patterns/peer-review/src/peer_review/llm_client.py
- _infra/smart_proxy.py indirectly via llm_client.SERVER_COMMANDS

The config lives in config/model_runtime.yaml so runtime flags can be changed
without editing Python or shell scripts.
"""

from __future__ import annotations

import argparse
import os
import shlex
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "model_runtime.yaml"


def _expand(value: Any, context: dict[str, str] | None = None) -> Any:
    if not isinstance(value, str):
        return value
    context = context or {}
    out = value.replace("${HOME}", str(Path.home()))
    for key, val in context.items():
        out = out.replace("${" + key + "}", val)
    return os.path.expandvars(out)


def load_runtime_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    server_dir = _expand(data.get("server_dir", "${HOME}/LocalAI/servers"))
    data["server_dir"] = server_dir
    return data


def _format_extra_args(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(shlex.quote(str(v)) for v in value if str(v).strip())
    return str(value)


def get_server_config(port: int) -> dict[str, Any]:
    cfg = load_runtime_config()
    servers = cfg.get("servers", {})
    raw = servers.get(str(port)) or servers.get(port)
    if not raw:
        raise KeyError(f"No model runtime server config for port {port}")
    context = {"server_dir": str(cfg["server_dir"])}
    out: dict[str, Any] = {}
    for key, value in raw.items():
        out[key] = _expand(value, context)
    out["port"] = port
    return out


def build_command(port: int) -> str:
    cfg = get_server_config(port)
    template = cfg["command_template"]
    fmt = dict(cfg)
    fmt["extra_args"] = _format_extra_args(cfg.get("extra_args", []))
    fmt["flash_attention_flag"] = "-fa on" if cfg.get("flash_attention") else ""
    return " ".join(template.format(**fmt).split())


def get_server_commands() -> dict[int, str]:
    cfg = load_runtime_config()
    return {int(port): build_command(int(port)) for port in cfg.get("servers", {})}


def get_kill_pattern(port: int) -> str:
    return str(get_server_config(port).get("kill_pattern", f".*{port}"))


def get_memory_required_gb(port: int) -> int:
    return int(get_server_config(port).get("memory_required_gb", 20))


def get_ollama_env() -> dict[str, str]:
    cfg = load_runtime_config()
    env = cfg.get("ollama", {}).get("env", {}) or {}
    return {str(k): str(_expand(v)) for k, v in env.items() if v is not None}


def get_ollama_command() -> str:
    cfg = load_runtime_config()
    return str(cfg.get("ollama", {}).get("command", "ollama serve"))


def print_env_shell(prefix: str = "") -> None:
    if prefix == "ollama":
        env = get_ollama_env()
    else:
        env = {}
    for key, value in env.items():
        print(f"export {key}={shlex.quote(value)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_cmd = sub.add_parser("command")
    p_cmd.add_argument("port", type=int)
    p_kill = sub.add_parser("kill-pattern")
    p_kill.add_argument("port", type=int)
    p_mem = sub.add_parser("memory-gb")
    p_mem.add_argument("port", type=int)
    p_env = sub.add_parser("env-shell")
    p_env.add_argument("scope", choices=["ollama"])
    sub.add_parser("ollama-command")
    args = parser.parse_args()

    if args.cmd == "command":
        print(build_command(args.port))
    elif args.cmd == "kill-pattern":
        print(get_kill_pattern(args.port))
    elif args.cmd == "memory-gb":
        print(get_memory_required_gb(args.port))
    elif args.cmd == "env-shell":
        print_env_shell(args.scope)
    elif args.cmd == "ollama-command":
        print(get_ollama_command())


if __name__ == "__main__":
    main()

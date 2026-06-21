# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 16:30:00 CST

"""
FORGE Network CLI 入口（增量）

当前支持：
- health

用法：
    python -m _infra.network.cli health
    python -m _infra.network.cli --help
"""

import argparse
import sys

from .health_check.checker import check_health, print_health_report
from .config_loader import load_network_config


def cmd_health(args):
    report = check_health()
    print_health_report(report)
    if report.status != "healthy":
        sys.exit(1)


def cmd_config(args):
    cfg = load_network_config()
    print("Network Config loaded successfully")
    print(f"  version: {cfg.version}")
    print(f"  searxng: {cfg.search.searxng.base_url}")
    print(f"  privacy qwen: {cfg.privacy_gateway.qwen_model}")


def main():
    parser = argparse.ArgumentParser(
        prog="forge-network",
        description="FORGE Network tooling (incremental module)"
    )
    subparsers = parser.add_subparsers(dest="command")

    # health
    p_health = subparsers.add_parser("health", help="Run health checks")
    p_health.set_defaults(func=cmd_health)

    # config
    p_config = subparsers.add_parser("config", help="Show loaded network config")
    p_config.set_defaults(func=cmd_config)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

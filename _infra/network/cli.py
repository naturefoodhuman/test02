# Arena.ai Agent Mode - Execution Lead Engineer
# Created at: 2026-06-23 18:35:00 CST

"""
FORGE Network CLI 入口（增量）

当前支持：
- health: 运行健康检查
- config: 显示配置
- search: 执行完整联网搜索流 (WorkFlow)

用法：
    python -m _infra.network.cli health
    python -m _infra.network.cli config
    python -m _infra.network.cli search "你的问题" --mode research
"""

import argparse
import asyncio
import sys
import json

from .health_check.checker import check_health, print_health_report
from .config_loader import load_network_config
from .network_workflow.workflow import NetworkWorkflow


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
    print(f"  rag db: {cfg.local_rag.rag_db}")


async def async_cmd_search(args):
    """异步执行搜索流"""
    workflow = NetworkWorkflow()
    try:
        result = await workflow.execute(args.query, mode=args.mode)
        
        if args.json:
            print(result.model_dump_json(indent=2))
            return

        print(f"\n[QUERY]: {result.query}")
        print(f"[MODE]: {result.mode}")
        print("-" * 40)
        print(f"\n{result.anonymized_content}\n")
        print("-" * 40)
        
        if result.citations:
            print("\n[CITATIONS]:")
            for i, cit in enumerate(result.citations, 1):
                print(f"  [{i}] {cit['title']}")
                print(f"      {cit['url']}")
        
        if result.tokens_removed > 0:
            print(f"\n[PRIVACY]: Removed {result.tokens_removed} PII entities.")

    except Exception as e:
        print(f"Workflow Error: {e}", file=sys.stderr)
        sys.exit(2)


def cmd_search(args):
    """同步包装器"""
    asyncio.run(async_cmd_search(args))


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

    # search
    p_search = subparsers.add_parser("search", help="Execute network search workflow")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--mode", choices=["research", "coding"], default="research", help="Search mode")
    p_search.add_argument("--json", action="store_true", help="Output result as JSON")
    p_search.set_defaults(func=cmd_search)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()

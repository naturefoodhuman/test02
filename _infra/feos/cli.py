# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""FEOS CLI entrypoint."""

from __future__ import annotations

import argparse
import json
import sys

from _infra.feos.bootstrap import bootstrap_feos
from _infra.feos.case_manager import CreateCaseInput
from _infra.feos.facade import FEOSFacade


def build_facade() -> FEOSFacade:
    context = bootstrap_feos(create_home=True)
    return context.facade  # type: ignore[attr-defined]


def print_result(data, as_json: bool = False) -> None:
    if as_json:
        if hasattr(data, "to_dict"):
            print(json.dumps(data.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(data)


def cmd_create(args) -> int:
    facade = build_facade()
    result = facade.create_case(CreateCaseInput(title=args.title, user_goal=args.user_goal, task_id=args.task_id, actor="cli"))
    if not result.ok:
        print(f"operation=create error={'; '.join(result.errors)} hint=check title/user-goal", file=sys.stderr)
        return 2
    case = result.value
    if args.json:
        print_result(case, as_json=True)
    else:
        print(f"created {case.id} status={case.status}")
    return 0


def cmd_status(args) -> int:
    facade = build_facade()
    result = facade.get_case(args.case_id)
    if not result.ok:
        print(f"operation=status error={'; '.join(result.errors)} hint=check case_id", file=sys.stderr)
        return 2
    case = result.value
    if args.json:
        print_result(case, as_json=True)
    else:
        print(f"{case.id} status={case.status} title={case.title}")
    return 0


def cmd_list(args) -> int:
    facade = build_facade()
    result = facade.list_cases()
    if not result.ok:
        print(f"operation=list error={'; '.join(result.errors)} hint=check FEOS_HOME", file=sys.stderr)
        return 2
    cases = result.value or []
    if args.json:
        print(json.dumps([case.to_dict() for case in cases], ensure_ascii=False, indent=2))
    else:
        for case in cases:
            print(f"{case.id}\t{case.status}\t{case.title}")
    return 0


def cmd_archive(args) -> int:
    facade = build_facade()
    try:
        case = facade.case_service.transition_case(args.case_id, "Archived", actor="cli")
    except Exception as exc:
        print(f"operation=archive error={exc} hint=only terminal/abandoned cases can archive", file=sys.stderr)
        return 2
    if args.json:
        print_result(case, as_json=True)
    else:
        print(f"archived {case.id}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="feos", description="FORGE Escalation OS CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="Create an escalation case")
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--user-goal", required=True)
    p_create.add_argument("--task-id")
    p_create.add_argument("--json", action="store_true")
    p_create.set_defaults(func=cmd_create)

    p_status = sub.add_parser("status", help="Show case status")
    p_status.add_argument("case_id")
    p_status.add_argument("--json", action="store_true")
    p_status.set_defaults(func=cmd_status)

    p_list = sub.add_parser("list", help="List cases")
    p_list.add_argument("--json", action="store_true")
    p_list.set_defaults(func=cmd_list)

    p_archive = sub.add_parser("archive", help="Archive a case")
    p_archive.add_argument("case_id")
    p_archive.add_argument("--json", action="store_true")
    p_archive.set_defaults(func=cmd_archive)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

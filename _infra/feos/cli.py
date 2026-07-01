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
from _infra.feos.workflows import ClipboardEscalationWorkflow, ResponseProcessingWorkflow, ExecutionClosureWorkflow
from _infra.feos.ingestion import ResponseIngestionService
from _infra.feos.verification import VerificationService
from _infra.feos.execution import ExecutionService, OutcomeEvaluator
from _infra.feos.distillation import KnowledgeDistillationService, KnowledgeWriter
from _infra.feos.repositories import ResponseRepository, VerificationRepository, ExecutionRepository, KnowledgeRepository


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



def _ctx():
    return bootstrap_feos(create_home=True)


def cmd_collect(args) -> int:
    ctx = _ctx(); case = ctx.case_service.get_case(args.case_id)
    ev = ClipboardEscalationWorkflow(ctx.workspace, ctx.project_root).collect(case)
    print(f"collected {len(ev)} evidence")
    return 0


def cmd_graph_build(args) -> int:
    ctx = _ctx(); case = ctx.case_service.get_case(args.case_id)
    ev = ClipboardEscalationWorkflow(ctx.workspace, ctx.project_root).collect(case)
    graph = ClipboardEscalationWorkflow(ctx.workspace, ctx.project_root).build_graph(args.case_id, ev)
    print(f"graph {graph.id} nodes={len(graph.nodes)} edges={len(graph.edges)}")
    return 0


def cmd_context_compile(args) -> int:
    ctx = _ctx(); case = ctx.case_service.get_case(args.case_id)
    wf = ClipboardEscalationWorkflow(ctx.workspace, ctx.project_root)
    ev = wf.collect(case); context = wf.compile_context(case, ev)
    print(f"context {context.id} tokens={context.token_estimate}")
    return 0


def cmd_export(args) -> int:
    ctx = _ctx(); case = ctx.case_service.get_case(args.case_id)
    result = ClipboardEscalationWorkflow(ctx.workspace, ctx.project_root).run_until_export(case, provider=args.provider)
    print(result["export"].get("clipboard_md"))
    return 0


def cmd_clipboard_copy(args) -> int:
    ctx = _ctx()
    from _infra.feos.gateways import ClipboardGateway
    session = ClipboardGateway(ctx.workspace).dispatch_copy(args.case_id)
    print(f"copied session={session.id}")
    return 0


def cmd_import_response(args) -> int:
    ctx = _ctx()
    if args.response_file:
        raw = open(args.response_file, encoding="utf-8").read()
    else:
        raw = sys.stdin.read()
    response = ResponseIngestionService(ResponseRepository(ctx.workspace)).import_text(args.case_id, raw)
    print(response.id)
    return 0


def _latest_response(ctx, case_id: str):
    resp_dir = ctx.workspace.case_dir(case_id) / "response"
    files = sorted(resp_dir.glob("resp_*.yaml"))
    if not files:
        raise RuntimeError("no response metadata found")
    from _infra.feos.models import ExternalResponse
    return ExternalResponse.from_yaml_file(files[-1])


def cmd_response_parse(args) -> int:
    ctx = _ctx(); response = _latest_response(ctx, args.case_id)
    parsed = ResponseIngestionService(ResponseRepository(ctx.workspace)).parse_response(response)
    print(parsed.id)
    return 0


def _latest_parsed(ctx, case_id: str):
    resp_dir = ctx.workspace.case_dir(case_id) / "response"
    files = sorted(resp_dir.glob("*_parsed.yaml"))
    if not files:
        raise RuntimeError("no parsed response found")
    from _infra.feos.models import ParsedResponse
    return ParsedResponse.from_yaml_file(files[-1])


def cmd_verify(args) -> int:
    ctx = _ctx(); parsed = _latest_parsed(ctx, args.case_id)
    result = VerificationService(VerificationRepository(ctx.workspace)).verify(parsed)
    print(f"{result.id} status={result.status}")
    return 0


def _latest_verification(ctx, case_id: str):
    ver_dir = ctx.workspace.case_dir(case_id) / "verification"
    files = sorted(ver_dir.glob("ver_*.yaml"))
    if not files:
        raise RuntimeError("no verification found")
    from _infra.feos.models import VerificationResult
    return VerificationResult.from_yaml_file(files[-1])


def cmd_plan(args) -> int:
    ctx = _ctx(); parsed = _latest_parsed(ctx, args.case_id); ver = _latest_verification(ctx, args.case_id)
    plan = ExecutionService(ExecutionRepository(ctx.workspace)).create_plan(parsed, ver)
    print(plan.id if plan else "no_plan")
    return 0


def cmd_outcome(args) -> int:
    ctx = _ctx(); outcome = OutcomeEvaluator().record(args.case_id, args.status, args.summary)
    ExecutionRepository(ctx.workspace).put_yaml(args.case_id, "outcome", outcome.to_dict())
    print(outcome.id)
    return 0


def cmd_distill(args) -> int:
    ctx = _ctx(); case = ctx.case_service.get_case(args.case_id)
    from _infra.feos.models import Outcome
    outcome_path = ctx.workspace.case_dir(args.case_id) / "execution" / "outcome.yaml"
    outcome = Outcome.from_yaml_file(outcome_path)
    candidate = KnowledgeDistillationService(KnowledgeWriter(KnowledgeRepository(ctx.workspace))).distill(case, outcome, [])
    print(candidate.id if candidate else "no_candidate")
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

    p_collect = sub.add_parser("collect")
    p_collect.add_argument("case_id")
    p_collect.set_defaults(func=cmd_collect)

    p_graph = sub.add_parser("graph")
    graph_sub = p_graph.add_subparsers(dest="graph_cmd", required=True)
    p_graph_build = graph_sub.add_parser("build")
    p_graph_build.add_argument("case_id")
    p_graph_build.set_defaults(func=cmd_graph_build)

    p_context = sub.add_parser("context")
    context_sub = p_context.add_subparsers(dest="context_cmd", required=True)
    p_context_compile = context_sub.add_parser("compile")
    p_context_compile.add_argument("case_id")
    p_context_compile.add_argument("--target", default="chatgpt_web")
    p_context_compile.set_defaults(func=cmd_context_compile)

    p_export = sub.add_parser("export")
    p_export.add_argument("case_id")
    p_export.add_argument("--gateway", default="clipboard")
    p_export.add_argument("--provider", default="chatgpt_web")
    p_export.set_defaults(func=cmd_export)

    p_clip = sub.add_parser("clipboard")
    clip_sub = p_clip.add_subparsers(dest="clip_cmd", required=True)
    p_clip_copy = clip_sub.add_parser("copy")
    p_clip_copy.add_argument("case_id")
    p_clip_copy.set_defaults(func=cmd_clipboard_copy)

    p_import = sub.add_parser("import")
    import_sub = p_import.add_subparsers(dest="import_cmd", required=True)
    p_import_resp = import_sub.add_parser("response")
    p_import_resp.add_argument("case_id")
    p_import_resp.add_argument("--response-file")
    p_import_resp.set_defaults(func=cmd_import_response)

    p_response = sub.add_parser("response")
    response_sub = p_response.add_subparsers(dest="response_cmd", required=True)
    p_response_parse = response_sub.add_parser("parse")
    p_response_parse.add_argument("case_id")
    p_response_parse.set_defaults(func=cmd_response_parse)

    p_verify = sub.add_parser("verify")
    p_verify.add_argument("case_id")
    p_verify.set_defaults(func=cmd_verify)

    p_plan = sub.add_parser("plan")
    p_plan.add_argument("case_id")
    p_plan.set_defaults(func=cmd_plan)

    p_outcome = sub.add_parser("outcome")
    outcome_sub = p_outcome.add_subparsers(dest="outcome_cmd", required=True)
    p_outcome_eval = outcome_sub.add_parser("evaluate")
    p_outcome_eval.add_argument("case_id")
    p_outcome_eval.add_argument("--status", default="resolved")
    p_outcome_eval.add_argument("--summary", default="resolved by user")
    p_outcome_eval.add_argument("--outcome-file")
    p_outcome_eval.set_defaults(func=cmd_outcome)

    p_distill = sub.add_parser("distill")
    p_distill.add_argument("case_id")
    p_distill.set_defaults(func=cmd_distill)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

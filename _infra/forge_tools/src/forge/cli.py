# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
"""forge CLI：在项目目录内驱动五阶段流程的轻量命令行工具。

零第三方依赖（只用标准库 argparse），保证在任何 Python 3.11+ 环境可跑。

命令：
  forge status            查看当前阶段与任务图概览
  forge check             校验 TASK_GRAPH（status/依赖/循环）+ 当前阶段退出产物
  forge tasks             列出可执行任务（依赖已满足）
  forge advance           检查能否进入下一阶段（不自动改文件，只给结论）
  forge gate <id>         打印某个 HITL Gate 的说明与所需文档

约定：在项目根目录运行（含 docs/ 的目录）。用 --root 指定其它根。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from forge.phases import PHASE_DEFS, PHASES, can_advance, next_phase
from forge.task_graph import load_task_graph, validate_task_graph

GATE_DESC = {
    "GATE-1": "需求确认：需求边界由人定义，AI 只能辅助。",
    "GATE-2": "架构与技术选型确认：选型决策必须人工审批。",
    "GATE-3": "风险清单确认：对风险的接受度由人决定。",
    "GATE-4": "最终验收：交付质量的最终判断权在人。",
    "GATE-5": "知识库更新确认：写入 _factory/ 的内容必须人工审核。",
}


def _existing_files(root: Path) -> set[str]:
    """收集项目内相对路径集合（用于退出产物检查）。"""
    out: set[str] = set()
    for p in root.rglob("*"):
        if p.is_file():
            out.add(str(p.relative_to(root)))
    return out


def _detect_phase(root: Path) -> str:
    """根据已存在产物粗略推断当前阶段（从后往前找最先满足进入条件的阶段）。"""
    files = _existing_files(root)
    # 从最后阶段倒推：哪个阶段的进入文档齐全且其退出产物尚不全，就认为在那个阶段
    for ph in reversed(PHASES):
        pdef = PHASE_DEFS[ph]
        entry_ok = all(d in files for d in pdef.entry_docs)
        ok_advance, _ = can_advance(ph, files)
        if entry_ok and not ok_advance:
            return ph
    return "DISCOVERY"


def cmd_status(root: Path) -> int:
    phase = _detect_phase(root)
    print(f"📍 推断当前阶段：{phase}")
    tg_path = root / "docs" / "TASK_GRAPH.md"
    if tg_path.exists():
        g = load_task_graph(tg_path)
        from collections import Counter

        c = Counter(t.status for t in g.tasks)
        print(f"📊 任务图：共 {len(g.tasks)} 个任务  {dict(c)}")
    else:
        print("ℹ️  未找到 docs/TASK_GRAPH.md")
    return 0


def cmd_check(root: Path) -> int:
    rc = 0
    tg_path = root / "docs" / "TASK_GRAPH.md"
    if tg_path.exists():
        g = load_task_graph(tg_path)
        problems = validate_task_graph(g)
        ip = g.in_progress()
        if problems:
            rc = 1
            print("❌ TASK_GRAPH 校验失败：")
            for p in problems:
                print(f"   - {p}")
        else:
            print("✅ TASK_GRAPH 结构合法。")
        if ip:
            print(f"⚠️  存在 {len(ip)} 个 IN_PROGRESS 任务（提交前应改为 DONE）：")
            for t in ip:
                print(f"   - {t.name}")
    else:
        print("ℹ️  无 docs/TASK_GRAPH.md，跳过任务图校验。")

    phase = _detect_phase(root)
    ok, missing = can_advance(phase, _existing_files(root))
    if ok:
        print(f"✅ 阶段 {phase} 的退出产物齐全。")
    else:
        print(f"⚠️  阶段 {phase} 缺少退出产物：{missing}")
    return rc


def cmd_tasks(root: Path) -> int:
    tg_path = root / "docs" / "TASK_GRAPH.md"
    if not tg_path.exists():
        print("ℹ️  无 docs/TASK_GRAPH.md")
        return 0
    g = load_task_graph(tg_path)
    ready = g.ready()
    if not ready:
        print("（无可执行任务：要么都做完了，要么依赖未满足）")
        return 0
    print("🟢 可执行任务（依赖已满足）：")
    for t in ready:
        print(f"   - {t.name}")
    return 0


def cmd_advance(root: Path) -> int:
    phase = _detect_phase(root)
    ok, missing = can_advance(phase, _existing_files(root))
    nxt = next_phase(phase)
    if not ok:
        print(f"⛔ 当前阶段 {phase} 退出产物不全，不能前进。缺：{missing}")
        return 1
    gate = PHASE_DEFS[phase].hitl_gate
    if nxt is None:
        print(f"🏁 当前已是最后阶段 {phase}。")
    else:
        print(f"✅ 可从 {phase} 进入 {nxt}。")
    if gate:
        print(f"🚦 但需先通过人工门控 {gate}：{GATE_DESC.get(gate, '')}")
    return 0


def cmd_gate(gate_id: str) -> int:
    gid = gate_id.upper()
    if gid in GATE_DESC:
        print(f"🚦 {gid}：{GATE_DESC[gid]}")
        return 0
    print(f"未知 Gate：{gate_id}（可选 GATE-1..GATE-5）")
    return 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="forge", description="FORGE Factory CLI")
    p.add_argument("--root", default=".", help="项目根目录（含 docs/）")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="当前阶段与任务图概览")
    sub.add_parser("check", help="校验任务图与退出产物")
    sub.add_parser("tasks", help="列出可执行任务")
    sub.add_parser("advance", help="检查能否进入下一阶段")
    g = sub.add_parser("gate", help="打印某 HITL Gate 说明")
    g.add_argument("gate_id")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    if args.cmd == "status":
        return cmd_status(root)
    if args.cmd == "check":
        return cmd_check(root)
    if args.cmd == "tasks":
        return cmd_tasks(root)
    if args.cmd == "advance":
        return cmd_advance(root)
    if args.cmd == "gate":
        return cmd_gate(args.gate_id)
    return 2


if __name__ == "__main__":
    sys.exit(main())

# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-13 23:55:00 CST
"""debt CLI：个人合法讨债助手命令行入口（v1.1.0 LangGraph + 双文件模型管理体系）。

命令：
  debt add        录入一笔债务
  debt list       列出所有债务 + 时效预警
  debt intel      给某笔债务加情报
  debt timeline   看某笔债务的案件时间线
  debt acquire    为某笔债务的债务人生成官方渠道待查清单
  debt report     生成/更新某笔债务的策略报告(GLM优先,离线兜底)
  debt review     FB-14: Peer-Review 多专家评审 (LangGraph + HUB-SPOKE)
  debt continue   从 HITL 人工审核中断点恢复评审
"""
from __future__ import annotations

import argparse
import sys
import os
import traceback
from pathlib import Path

# 项目根目录：本文件位于 projects/debt-collection/src/debt/cli.py
ROOT = Path(__file__).resolve().parents[4]

from debt import intel as intel_mod
from debt import ledger
from debt.integrations import build_acquisition_plan
from debt.models import (
    Debt, DebtNature, Intel, IntelCredibility, Store, mask_id,
)
from debt.strategy import generate_report
from debt.timeline import build_timeline, prescription_status

# Peer-Review 平台层（LangGraph v1.1.0）
from peer_review.platform.data_privacy_gate import DataPrivacyGate
from peer_review.platform.memory_store import MemoryStore, ModelRunRecord
from peer_review.platform.routing_plan_engine import RoutingPlanEngine


def _store(args) -> Store:
    return Store(db_path=args.db)


def _extract_privacy_fields(d: Debt) -> dict:
    """从 Debt 模型提取隐私策略字段（映射到 privacy_policy.yaml 中的字段名）"""
    fields = {
        "debtor_region": d.debtor_region,
    }
    if d.debtor_name:
        fields["debtor_name"] = d.debtor_name
    if d.debtor_id:
        fields["id_number"] = d.debtor_id
    if d.amount:
        fields["amount"] = d.amount
    if d.evidence:
        fields["case_evidence"] = ", ".join(d.evidence)
    return fields


def _plan_uses_api(project_root: Path, plan_id: str | None) -> bool:
    """检查指定方案是否使用任何 API 模型（即数据可能出境）"""
    engine = RoutingPlanEngine(project_root)
    if plan_id and plan_id in engine.config.routing.plans:
        engine.config.routing.active_plan = plan_id
    plan = engine.get_active_plan()
    for node_cfg in plan.nodes.values():
        model_cfg = engine.config.models.models.get(node_cfg.model)
        if model_cfg and model_cfg.type.value == "api":
            return True
    return False


def _estimate_cost(plan_id: str, project_root: Path) -> float:
    """从 routing_plans.yaml 的 estimated_cost 字段提取预估成本（USD）"""
    engine = RoutingPlanEngine(project_root)
    plan = engine.config.routing.plans.get(plan_id or engine.config.routing.active_plan)
    if not plan:
        return 0.0
    cost_str = plan.estimated_cost
    # 示例：$0.01-0.03/次 或 $0.05-0.15/次 或 $0.005/次 或 $0
    import re
    nums = re.findall(r"[0-9.]+", cost_str)
    if not nums:
        return 0.0
    if len(nums) == 1:
        return float(nums[0])
    return (float(nums[0]) + float(nums[1])) / 2


def cmd_add(args) -> int:
    s = _store(args)
    did = ledger.add_debt(s, Debt(
        debtor_name=args.name, amount=args.amount,
        nature=DebtNature(args.nature), debtor_id=args.id, debtor_region=args.region,
        lend_date=args.lend, due_date=args.due, last_contact_date=args.contact,
        evidence=args.evidence.split(",") if args.evidence else [],
    ))
    print(f"✅ 已录入债务 #{did}：{args.name} {args.amount}元（身份证 {mask_id(args.id)}）")
    s.close()
    return 0


def cmd_list(args) -> int:
    s = _store(args)
    debts = ledger.list_debts(s)
    if not debts:
        print("（暂无债务，用 debt add 录入）")
        s.close()
        return 0
    print(f"📋 共 {len(debts)} 笔，未还总额 {ledger.total_outstanding(s)} 元：")
    for d in debts:
        st = prescription_status(d)
        print(f"  #{d.id} {d.debtor_name} 未还{d.outstanding}元 [{d.stage.value}] 时效:{st.level}({st.days_left}天)")
    s.close()
    return 0


def cmd_intel(args) -> int:
    s = _store(args)
    iid = intel_mod.add_intel(s, Intel(
        debt_id=args.debt, content=args.content, source=args.source,
        credibility=IntelCredibility(args.credibility), affects_strategy=not args.no_affect,
    ))
    print(f"✅ 已为债务 #{args.debt} 添加情报 #{iid}：{args.content}")
    if not args.no_affect:
        print("   该情报会影响策略，建议运行：debt review --debt", args.debt, "重新评估")
    s.close()
    return 0


def cmd_timeline(args) -> int:
    s = _store(args)
    d = ledger.get_debt(s, args.debt)
    if not d:
        print(f"❌ 找不到债务 #{args.debt}")
        s.close()
        return 1
    items = intel_mod.list_intel(s, args.debt)
    print(f"🗓 债务 #{args.debt} {d.debtor_name} 案件时间线：")
    for e in build_timeline(d, items):
        print(f"  {e.when or '????-??-??'} [{e.kind}] {e.summary}")
    s.close()
    return 0


def cmd_acquire(args) -> int:
    s = _store(args)
    d = ledger.get_debt(s, args.debt)
    if not d:
        print(f"❌ 找不到债务 #{args.debt}")
        s.close()
        return 1
    res = build_acquisition_plan(d.debtor_name, region=d.debtor_region, out_dir=args.out)
    if not res["ok"]:
        print("⚠️", res["error"])
        s.close()
        return 1
    print(f"📋 为 {d.debtor_name} 生成官方渠道待查清单（{len(res['tasks'])} 项）：")
    for t in res["tasks"]:
        flags = []
        if t["needs_captcha"]: flags.append("验证码")
        if t["needs_login"]: flags.append("登录")
        print(f"  - {t['source']} {('['+'/'.join(flags)+']') if flags else ''}")
    print(f"📁 清单：{res['checklist_md']}")
    print("⚠️ 遇验证码/登录请手动完成；不暴力绕过、不替你登录账号。")
    s.close()
    return 0


def cmd_report(args) -> int:
    s = _store(args)
    d = ledger.get_debt(s, args.debt)
    if not d:
        print(f"❌ 找不到债务 #{args.debt}")
        s.close()
        return 1
    items = intel_mod.list_intel(s, args.debt)
    from debt.llm_client import LLMConfig
    cfg = LLMConfig(model=args.model)
    if args.model.startswith("local"):
        print(f"🔒 隐私模式：用本地模型 {args.model}，案件事实不出本机。")
    else:
        print(f"☁️ 质量模式：用 {args.model}（案件事实会发送到云端推理）。")
    rep = generate_report(d, items, cfg=cfg, update_reason=args.reason or "")
    print("=" * 60)
    print(rep.body)
    print("=" * 60)
    print(f"模型：{rep.model_used} | 合规：{'✅通过' if rep.compliance_passed else '⛔未通过'}")
    if not rep.compliance_passed:
        print(rep.compliance_note)
    s.close()
    return 0


def cmd_review(args) -> int:
    """FB-14: Peer-Review 多专家评审 (LangGraph v1.1.0)"""
    import time

    print("🔍 启动 Peer-Review 模块 (LangGraph)...")

    try:
        from peer_review.orchestrator import run_langgraph_review
        print("✅ peer_review 模块加载成功")
    except Exception as e:
        print(f"❌ 模块加载失败！")
        traceback.print_exc()
        return 1

    # 组装案件上下文
    from debt import intel as intel_mod
    from debt import ledger

    s = _store(args)
    d = ledger.get_debt(s, args.debt)
    if not d:
        print(f"❌ 找不到债务 #{args.debt}")
        s.close()
        return 1

    items = intel_mod.list_intel(s, args.debt)
    query_lines = [
        f"【案件事实】债务人：{d.debtor_name}，欠款：{d.outstanding}元",
        f"【债务性质】{d.nature.value if hasattr(d.nature, 'value') else d.nature}",
        f"【当前阶段】{d.stage.value if hasattr(d.stage, 'value') else d.stage}",
        f"【证据】{', '.join(d.evidence) if d.evidence else '无'}",
    ]
    if items:
        query_lines.append("\n【情报】")
        for it in items:
            cred = it.credibility.value if hasattr(it.credibility, 'value') else str(it.credibility)
            query_lines.append(f"  - [{it.source}/{cred}] {it.content}")

    query = "\n".join(query_lines)
    active_plan = args.plan or "default"
    print(f"\n🚀 激活方案: {active_plan}")

    # ── DataPrivacyGate 实时确认门 ──
    privacy_approved = False
    privacy_fields = _extract_privacy_fields(d)
    if _plan_uses_api(ROOT, args.plan):
        gate = DataPrivacyGate(ROOT / "config" / "privacy_policy.yaml")
        result = gate.check(privacy_fields, "chinese_api")

        if result.blocked_fields:
            print("\n⛔ 数据出境被阻断：")
            for field in result.blocked_fields:
                decision = next((dec for dec in result.decisions if dec.field == field), None)
                print(f"  • {field}: {decision.reason if decision else '策略禁止'}")
            print("\n请修改 privacy_policy.yaml 或选择 all-local 方案（数据完全不出本地）。")
            s.close()
            return 1

        if result.requires_human_fields:
            approved = DataPrivacyGate.request_human_approval(
                result.requires_human_fields,
                result.preview,
                "中国商业 API（DeepSeek/Qwen/GLM）",
            )
            if not approved:
                print("\n❌ 已取消数据出境，评审中止。")
                s.close()
                return 1
            print("\n✅ 数据出境已获人工确认。")
            privacy_approved = True
        else:
            privacy_approved = True
    else:
        privacy_approved = True

    # 运行 LangGraph 评审（计时）
    start_time = time.time()
    final_state = run_langgraph_review(
        query,
        project_root=ROOT,
        plan_id=args.plan,
        data_fields=privacy_fields,
        privacy_endpoint="chinese_api" if _plan_uses_api(ROOT, args.plan) else "local_model",
        privacy_approved=privacy_approved,
    )
    elapsed = int(time.time() - start_time)

    print("\n" + "=" * 60)
    print("【主专家分析】")
    print(final_state.get("primary_analysis", "（无）"))
    print("\n【最终汇总结论】")
    print(final_state.get("consensus", "（无）"))

    if final_state.get("iron_gate_triggered"):
        print(f"\n⚠️ 铁闸触发：{final_state.get('iron_gate_reason', '')}")
    if final_state.get("requires_human"):
        print(f"\n⚠️ 分歧度 {final_state.get('divergence_score', 0)} 超过阈值，已触发人工审核中断点")
        print(f"   如需继续，请运行：debt continue {final_state.get('thread_id', 'UNKNOWN')}")

    print(f"\n🆔 线程 ID: {final_state.get('thread_id', 'UNKNOWN')}（可用于 debt continue 恢复）")
    print("=" * 60)

    # ── MemoryStore 记录运行 ──
    try:
        memory = MemoryStore(ROOT / "runtime" / "memory.db")
        import hashlib
        case_hash = hashlib.md5(query.encode("utf-8")).hexdigest()[:16]
        record = ModelRunRecord(
            run_id=f"{active_plan}-{case_hash}-{int(time.time())}",
            case_hash=case_hash,
            plan_id=active_plan,
            models_used=final_state.get("models_used", {}),
            total_time_seconds=elapsed,
            total_cost_usd=_estimate_cost(active_plan, ROOT),
            divergence_score=final_state.get("divergence_score", 0.0),
        )
        memory.record_run(record)
        print(f"\n📝 已记录运行到 MemoryStore：方案 {active_plan} | 耗时 {elapsed}s | 分歧度 {record.divergence_score}")
    except Exception as e:
        print(f"\n⚠️ MemoryStore 记录失败（非阻塞）: {e}")

    s.close()
    return 0


def cmd_continue(args) -> int:
    """从 HITL 人工审核中断点恢复 LangGraph 评审"""
    print(f"🔄 恢复评审线程: {args.thread_id}")
    try:
        from peer_review.orchestrator import continue_langgraph_review
        final_state = continue_langgraph_review(args.thread_id, project_root=ROOT)
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        traceback.print_exc()
        return 1

    print("\n" + "=" * 60)
    print("【主专家分析】")
    print(final_state.get("primary_analysis", "（无）"))
    print("\n【最终汇总结论】")
    print(final_state.get("consensus", "（无）"))

    if final_state.get("iron_gate_triggered"):
        print(f"\n⚠️ 铁闸触发：{final_state.get('iron_gate_reason', '')}")
    print("=" * 60)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="debt", description="个人合法讨债助手")
    p.add_argument("--db", default="runtime/debt.db", help="数据库路径(本地)")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="录入债务")
    a.add_argument("name"); a.add_argument("amount", type=float)
    a.add_argument("--nature", default="private_loan", choices=[n.value for n in DebtNature])
    a.add_argument("--id", default=""); a.add_argument("--region", default="")
    a.add_argument("--lend", default=""); a.add_argument("--due", default="")
    a.add_argument("--contact", default=""); a.add_argument("--evidence", default="")
    a.set_defaults(func=cmd_add)

    li = sub.add_parser("list", help="列出债务+时效"); li.set_defaults(func=cmd_list)

    it = sub.add_parser("intel", help="加情报")
    it.add_argument("debt", type=int); it.add_argument("content")
    it.add_argument("--source", default=""); it.add_argument("--credibility", default="medium",
                                                             choices=[c.value for c in IntelCredibility])
    it.add_argument("--no-affect", action="store_true")
    it.set_defaults(func=cmd_intel)

    tl = sub.add_parser("timeline", help="案件时间线"); tl.add_argument("debt", type=int)
    tl.set_defaults(func=cmd_timeline)

    ac = sub.add_parser("acquire", help="生成官方渠道待查清单")
    ac.add_argument("debt", type=int); ac.add_argument("--out", default="runtime/acquisition")
    ac.set_defaults(func=cmd_acquire)

    rp = sub.add_parser("report", help="生成/更新策略报告")
    rp.add_argument("debt", type=int); rp.add_argument("--reason", default="")
    rp.add_argument("--model", default="cloud/glm-primary")
    rp.set_defaults(func=cmd_report)

    rv = sub.add_parser("review", help="FB-14: Peer-Review 多专家评审 (LangGraph)")
    rv.add_argument("debt", type=int, help="债务ID")
    rv.add_argument("--plan", default=None,
                    help="临时指定 routing_plans.yaml 中的方案 ID（不修改配置文件）")
    rv.set_defaults(func=cmd_review)

    cont = sub.add_parser("continue", help="从 HITL 人工审核中断点恢复评审")
    cont.add_argument("thread_id", help="之前 debt review 返回的线程 ID")
    cont.set_defaults(func=cmd_continue)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

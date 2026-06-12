# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-12 01:30:00 CST
"""debt CLI：个人合法讨债助手命令行入口。

命令：
  debt add        录入一笔债务
  debt list       列出所有债务 + 时效预警
  debt intel      给某笔债务加情报
  debt timeline   看某笔债务的案件时间线
  debt acquire    为某笔债务的债务人生成官方渠道待查清单
  debt report     生成/更新某笔债务的策略报告(GLM优先,离线兜底)
零三方依赖（argparse + 标准库）。
"""
from __future__ import annotations

import argparse
import sys

from debt import intel as intel_mod
from debt import ledger
from debt.integrations import build_acquisition_plan
from debt.models import (
    Debt, DebtNature, Intel, IntelCredibility, Store, mask_id,
)
from debt.strategy import generate_report
from debt.timeline import build_timeline, prescription_status


def _store(args) -> Store:
    return Store(db_path=args.db)


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
        print("   该情报会影响策略，建议运行：debt report --debt", args.debt, "重新评估")
    s.close()
    return 0


def cmd_timeline(args) -> int:
    s = _store(args)
    d = ledger.get_debt(s, args.debt)
    if not d:
        print(f"❌ 找不到债务 #{args.debt}")
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
        return 1
    res = build_acquisition_plan(d.debtor_name, region=d.debtor_region, out_dir=args.out)
    if not res["ok"]:
        print("⚠️", res["error"])
        return 1
    print(f"📋 为 {d.debtor_name} 生成官方渠道待查清单（{len(res['tasks'])} 项）：")
    for t in res["tasks"]:
        flags = []
        if t["needs_captcha"]:
            flags.append("验证码")
        if t["needs_login"]:
            flags.append("登录")
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
        return 1
    items = intel_mod.list_intel(s, args.debt)
    # HARDEN 决策1：每次可选模型（敏感案件用本地不出本机，一般用 GLM 质量更高）
    from debt.llm_client import LLMConfig
    cfg = LLMConfig(model=args.model)
    if args.model.startswith("local"):
        print(f"🔒 隐私模式：用本地模型 {args.model}，案件事实不出本机。")
    else:
        print(f"☁️ 质量模式：用 {args.model}（案件事实会发送到云端推理，敏感案件建议改 --model local/primary）。")
    rep = generate_report(d, items, cfg=cfg, update_reason=args.reason or "")
    print("=" * 60)
    print(rep.body)
    print("=" * 60)
    print(f"模型：{rep.model_used} | 合规：{'✅通过' if rep.compliance_passed else '⛔未通过'}")
    if not rep.compliance_passed:
        print(rep.compliance_note)
    s.close()
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
    it.add_argument("--no-affect", action="store_true", help="该情报不影响策略")
    it.set_defaults(func=cmd_intel)

    tl = sub.add_parser("timeline", help="案件时间线"); tl.add_argument("debt", type=int)
    tl.set_defaults(func=cmd_timeline)

    ac = sub.add_parser("acquire", help="生成官方渠道待查清单")
    ac.add_argument("debt", type=int); ac.add_argument("--out", default="runtime/acquisition")
    ac.set_defaults(func=cmd_acquire)

    rp = sub.add_parser("report", help="生成/更新策略报告")
    rp.add_argument("debt", type=int); rp.add_argument("--reason", default="", help="动态更新原因(因哪条情报)")
    rp.add_argument("--model", default="cloud/glm-primary",
                    help="策略推理模型：cloud/glm-primary(质量,案件出云端) | local/primary(隐私,不出本机)")
    rp.set_defaults(func=cmd_report)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

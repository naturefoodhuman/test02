# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-11 23:10:00 CST
"""data-acquisition CLI：为债务人生成官方渠道取数待查清单。

用法：
  python -m acquisition.cli "张三" --type person --region 浙江杭州 -o ./out
  python -m acquisition.cli "某某公司" --type company -o ./out
零三方依赖（标准库 argparse）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from acquisition.models import Subject, SubjectType
from acquisition.planner import build_query_plan, save_plan
from acquisition.sources_registry import RiskLevel


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="acquisition", description="L1 取数：生成官方渠道待查清单(合规/不封号)")
    p.add_argument("name", help="债务人姓名/企业名称")
    p.add_argument("--type", choices=["person", "company"], default="person", help="对象类型")
    p.add_argument("--id", default="", help="身份证号/统一社会信用代码(敏感,本地处理)")
    p.add_argument("--region", default="", help="地域(辅助同名辨别)")
    p.add_argument("--max-risk", choices=["low", "medium", "high"], default="medium", help="允许最大风险")
    p.add_argument("-o", "--out", default="./acquisition_out", help="输出目录")
    p.add_argument("--l2", action="store_true",
                   help="启用 L2 浏览器辅助(人在环)：用 browser-use 接 GLM 半自动查询，遇验证码/登录停下等人工")
    p.add_argument("--bu-model", default="cloud/glm-primary",
                   help="L2 浏览器 Agent 用的模型(走 LiteLLM 网关)：cloud/glm-primary(默认/最稳) | local/primary(本地35b) | local/fallback(14b)")
    args = p.parse_args(argv)

    subject = Subject(
        name=args.name,
        subject_type=SubjectType.COMPANY if args.type == "company" else SubjectType.PERSON,
        id_number=args.id,
        region=args.region,
    )
    plan = build_query_plan(subject, max_risk=RiskLevel(args.max_risk))
    md, js = save_plan(plan, args.out)

    print(f"📋 已为『{args.name}』生成取数待查清单（{len(plan.tasks)} 项官方渠道）：")
    for i, t in enumerate(plan.tasks, 1):
        flags = []
        if t.needs_captcha:
            flags.append("验证码")
        if t.needs_login:
            flags.append("登录")
        fs = f"[{'/'.join(flags)}]" if flags else ""
        print(f"  {i}. {t.source_name} {fs} · 风险:{t.risk} · {t.access_mode}")
    print(f"\n📁 清单已写入：{md}")
    print("⚠️ 遇验证码/登录请你手动完成；系统不暴力绕过、不替你登录第三方账号（保账号安全+合规）。")

    # L2：浏览器辅助（人在环）
    if args.l2:
        from acquisition.browser_assist import BrowserAssistConfig, l2_available, run_l2_query
        from acquisition.planner import archive_results
        from acquisition.sources_registry import OFFICIAL_SOURCES

        cfg = BrowserAssistConfig(llm_model=args.bu_model)
        print(f"\n🌐 L2 浏览器辅助（人在环）· 模型={args.bu_model}：")
        if not l2_available():
            print("  ⚠️ 未安装 browser-use → L2 降级。真机安装：")
            print("     pip install browser-use playwright && playwright install chromium")
            print("     并确保 LiteLLM 网关(localhost:4000)在跑（模型驱动）。")
        results = []
        for t in plan.tasks:
            src = OFFICIAL_SOURCES.get(t.source_key)
            if src is None:
                continue
            print(f"  → 处理 {src.name} ...")
            r = run_l2_query(src, args.name, config=cfg)
            results.append(r)
            print(f"     {'✅ 查到' if r.found else 'ℹ️'} {r.summary[:80]}")
        arch = archive_results(results, args.out, args.name)
        print(f"  📁 L2 结果归档：{arch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

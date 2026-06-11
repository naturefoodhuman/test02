# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-11 23:10:00 CST
"""取数计划生成 + 结果归档（L1 取数层主逻辑）。

核心价值：给定一个债务人，自动生成"该去哪些官方渠道、查什么、怎么查"的
结构化待查清单；人工/半自动查完后，把结果结构化归档，供策略报告引用。
不暴力爬取，合规、不封号。
"""
from __future__ import annotations

import json
from pathlib import Path

from acquisition.models import QueryPlan, QueryResult, QueryTask, Subject, SubjectType
from acquisition.sources_registry import OFFICIAL_SOURCES, RiskLevel, list_sources


def build_query_plan(subject: Subject, *, max_risk: RiskLevel = RiskLevel.MEDIUM) -> QueryPlan:
    """为一个债务人生成取数待查清单。

    规则：
    - 自然人：查执行信息(zxgk) + 裁判文书(wenshu)；法条核对(flk)。
    - 企业/法人涉及：额外加工商(gsxt)。
    - 只纳入风险 ≤ max_risk 的官方渠道（默认排除 high 风险账号爬取）。

    Args:
        subject: 债务人。
        max_risk: 允许的最大风险等级。

    Returns:
        QueryPlan（含 tasks 列表）。
    """
    plan = QueryPlan(subject=subject)

    # 选择适用的数据源
    wanted: list[str] = ["zxgk", "wenshu", "flk"]
    if subject.subject_type == SubjectType.COMPANY:
        wanted.insert(2, "gsxt")
    else:
        # 自然人也常涉及其名下公司，gsxt 作为可选补充
        wanted.append("gsxt")

    allowed_keys = {s.key for s in list_sources(max_risk=max_risk)}

    for key in wanted:
        src = OFFICIAL_SOURCES.get(key)
        if src is None or key not in allowed_keys:
            continue
        plan.tasks.append(
            QueryTask(
                source_key=src.key,
                source_name=src.name,
                base_url=src.base_url,
                access_mode=src.access_mode.value,
                risk=src.risk.value,
                query_for=list(src.query_for),
                how_to=src.how_to,
                needs_captcha=src.needs_captcha,
                needs_login=src.needs_login,
            )
        )
    return plan


def save_plan(plan: QueryPlan, out_dir: str | Path) -> tuple[Path, Path]:
    """把取数计划落盘：待查清单 .md + 计划 .json。"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    safe = plan.subject.name.replace("/", "_")
    md = out / f"待查清单_{safe}.md"
    js = out / f"plan_{safe}.json"
    md.write_text(plan.to_checklist_md(), encoding="utf-8")
    js.write_text(plan.to_json(), encoding="utf-8")
    return md, js


def archive_results(results: list[QueryResult], out_dir: str | Path, subject_name: str) -> Path:
    """把人工/半自动查回的结果结构化归档为 JSON。

    Returns:
        归档文件路径。
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    safe = subject_name.replace("/", "_")
    path = out / f"results_{safe}.json"
    payload = {
        "subject": subject_name,
        "results": [r.to_dict() for r in results],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

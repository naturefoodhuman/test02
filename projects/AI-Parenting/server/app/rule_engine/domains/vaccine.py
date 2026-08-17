# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
#
# app/rule_engine/domains/vaccine.py —— 疫苗规划规则域（APC-T022）。
# 依据：ARCHITECTURE_FINAL §10.2（疫苗规则：中国国家免疫规划 + 自费疫苗衔接，版本化）、
#       §5.4（疫苗状态：planned/completed/delayed/skipped）；
#       FINAL_PRD §11.12（疫苗管理 P0：国家免疫规划 + 自费 + 预约/完成/逾期提醒 + 规则版本化；
#       提醒策略：提前14天可预约/提前3天准备/当天接种/逾期3天蓝/逾期14天黄；
#       早产/低体重儿保留胎龄和早产标记，稳定早产儿按实际月龄接种）；
#       ENGINEERING_DESIGN §13.2；TASK_BACKLOG APC-T022。
# 设计：VaccineRuleModule 实现 RuleModule Protocol（domain="vaccine"）。
#       规则包 YAML 定义 schedule（疫苗名 + 推荐接种天龄 + 剂次 + 是否国家免疫规划）。
#       evaluate 输入 baby_age_days + variables.vaccine_records（已接种/跳过）+ vaccine_region，
#       输出每个待办疫苗的 due_date/status/alert_level/evidence。
# 边界：只产出疫苗待办候选（架构 §10.2），不做医疗诊断、不出剂量。
#       早产儿接种规则由规则包配置（preterm_policy），本模块按配置执行。

"""疫苗规划规则域（APC-T022）。

``VaccineRuleModule`` 实现 ``RuleModule`` Protocol（``domain="vaccine"``）。

规则包 YAML（``config/rules/vaccine/cn-nip-2024.yaml``）定义中国国家免疫规划程序
（``schedule``：疫苗名 + 推荐接种天龄 + 剂次 + 是否国家免疫规划）。``evaluate`` 输入
``baby_age_days`` + ``variables.vaccine_records``（已接种/跳过记录）+ ``vaccine_region``，
输出每个待办疫苗的 ``due_date``/``status``/``alert_level``/``evidence``。

提醒策略（PRD §11.12）：
    - 提前 14 天 → ``upcoming``（可预约提醒）。
    - 提前 3 天 → ``due_soon``（准备提醒）。
    - 当天 → ``due``（接种提醒）。
    - 逾期 3 天 → ``overdue`` + 蓝色提醒。
    - 逾期 14 天 → ``overdue`` + 黄色提醒。

疫苗状态（§5.4）：``planned``/``completed``/``delayed``/``skipped``。已 completed/skipped
的疫苗不再产出待办。早产/低体重儿保留胎龄标记（PRD §11.12），稳定早产儿按实际月龄接种
（规则包 ``preterm_policy`` 配置，默认 ``actual_age``）。

输出（``outputs``）：``todos``（待办列表，每项含 ``vaccine``/``dose``/``due_date``/
``status``/``alert_level``/``days_offset``）+ ``region`` + ``rule_version``。
``evidence`` 含 rule_id + policy_version + 文本（§15.4）。
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from ..domain.models import (
    EvidenceRef,
    RuleContext,
    RuleDomain,
    RuleInput,
    RulePack,
    RuleResult,
)

# 提醒策略阈值（天，PRD §11.12）。
UPCOMING_DAYS = 14  # 提前 14 天可预约提醒。
DUE_SOON_DAYS = 3  # 提前 3 天准备提醒。
OVERDUE_BLUE_DAYS = 3  # 逾期 3 天蓝色提醒。
OVERDUE_YELLOW_DAYS = 14  # 逾期 14 天黄色提醒。


class VaccineRuleModule:
    """疫苗规划规则模块（APC-T022，domain="vaccine"）。

    国家免疫规划程序从规则包 YAML 加载（``schedule``）。``evaluate`` 按 baby_age_days
    与已接种记录计算每个待办疫苗的 due_date/status/alert_level。规则包版本化（§13.2）。
    """

    domain: RuleDomain = "vaccine"

    def __init__(self, pack: RulePack) -> None:
        self._pack = pack
        self._rule_version = f"{pack.policy_type}@{pack.version}"
        self._schedule: list[dict[str, Any]] = []
        for rule in pack.rules:
            # 每条 rule = 一个疫苗剂次；conditions 匹配 variables.vaccine（剂次标识 "name:dose"）。
            identifier = _extract_vaccine_match(rule.conditions)
            if identifier is not None:
                entry = dict(rule.action.outputs)
                # 拆 "name:dose" → vaccine=name（不含剂次），与 vaccine_records 元组对齐。
                vaccine_name, dose_from_id = _split_identifier(identifier)
                entry["vaccine"] = vaccine_name
                if not entry.get("dose"):
                    entry["dose"] = dose_from_id
                entry["evidence_text"] = rule.action.evidence_text
                self._schedule.append(entry)

    async def evaluate(self, input_: RuleInput, ctx: RuleContext) -> RuleResult:
        """计算疫苗待办列表 → RuleResult（todos + region + evidence）。"""
        # region：variables.vaccine_region 优先（baby.vaccine_region 权威，调用方注入），
        # ctx.region 兜底，默认 CN（PRD §11.12 baby.vaccine_region 默认 CN）。
        region = _str_or(input_.variables.get("vaccine_region"), _str_or(ctx.region, "CN"))
        baby_age_days = input_.baby_age_days
        now = ctx.now.date() if ctx.now else date.today()
        records = _collect_records(input_.variables.get("vaccine_records"))

        todos: list[dict[str, Any]] = []
        for entry in self._schedule:
            vaccine = str(entry["vaccine"])
            dose = _as_int(entry.get("dose")) or 1
            recommended_days = _as_int(entry.get("recommended_age_days"))
            if recommended_days is None:
                continue  # 缺推荐天龄的条目跳过（规则包配置不全）。

            # 已完成或跳过该剂次 → 不产出待办。
            status_record = records.get((vaccine, dose))
            if status_record in ("completed", "skipped"):
                continue

            due_date = now + timedelta(days=(recommended_days - (baby_age_days or 0)))
            days_offset = (due_date - now).days  # 正=未到期，负=已逾期。
            alert_level, status = _classify(days_offset)

            todos.append(
                {
                    "vaccine": vaccine,
                    "dose": dose,
                    "due_date": due_date.isoformat(),
                    "status": status,
                    "alert_level": alert_level,
                    "days_offset": days_offset,
                    "is_nip": bool(entry.get("is_nip", True)),
                }
            )

        # 按到期日升序排序（最紧迫在前）。
        todos.sort(key=lambda t: t["days_offset"])

        evidence_text = f"疫苗规划（{region}）：{len(todos)} 项待办（PRD §11.12）"
        return RuleResult(
            verdict="info",  # 疫苗待办为 info/reminder，不阻断。
            outputs={"todos": todos, "region": region},
            evidence=[
                EvidenceRef(
                    rule_id="vaccine",
                    policy_version=ctx.policy_version,
                    text=evidence_text,
                )
            ],
            rule_version=self._rule_version,
            reason_code="vaccine_plan",
        )


# ---- 辅助 ----


def _classify(days_offset: int) -> tuple[str, str]:
    """按距到期日天数 → (alert_level, status)（PRD §11.12 提醒策略）。"""
    if days_offset < -OVERDUE_YELLOW_DAYS:
        # 逾期超过 14 天 → 黄色提醒（仍 overdue，更紧迫）。
        return "yellow", "overdue"
    if days_offset < -OVERDUE_BLUE_DAYS:
        # 逾期 3~14 天 → 蓝色提醒。
        return "blue", "overdue"
    if days_offset < 0:
        # 逾期 0~3 天 → 蓝色提醒（当天起算）。
        return "blue", "overdue"
    if days_offset == 0:
        # 当天到期 → 接种提醒（蓝色）。
        return "blue", "due"
    if days_offset <= DUE_SOON_DAYS:
        # 提前 1~3 天 → 准备提醒（蓝色）。
        return "blue", "due_soon"
    if days_offset <= UPCOMING_DAYS:
        # 提前 4~14 天 → 可预约提醒（蓝色）。
        return "blue", "upcoming"
    # 远期（>14 天）→ 无提醒。
    return "info", "planned"


def _extract_vaccine_match(conditions: list) -> str | None:
    """从 rule.conditions 取 variables.vaccine 的 eq 匹配值（剂次标识）。"""
    for cond in conditions:
        if cond.op == "eq" and cond.field == "variables.vaccine":
            return str(cond.value)
    return None


def _split_identifier(identifier: str) -> tuple[str, int]:
    """拆剂次标识 "name:dose" → (vaccine_name, dose)。

    无 ":dose" 后缀时 dose=1。dose 解析失败也回退 1。
    """
    if ":" in identifier:
        name, _, dose_str = identifier.partition(":")
        try:
            return name, int(dose_str)
        except ValueError:
            return name, 1
    return identifier, 1


def _collect_records(raw: Any) -> dict[tuple[str, int], str]:
    """从 variables.vaccine_records 收集已接种/跳过记录 → {(vaccine, dose): status}。

    raw 支持两种形式：
        - list[dict]：``[{"vaccine": "bcg", "dose": 1, "status": "completed"}, ...]``
        - dict：``{"bcg:1": "completed", "hepb:1": "skipped"}``（key=vaccine:dose）
    """
    records: dict[tuple[str, int], str] = {}
    if raw is None:
        return records
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            vaccine = item.get("vaccine")
            dose = _as_int(item.get("dose")) or 1
            status = str(item.get("status", ""))
            if vaccine and status:
                records[(str(vaccine), dose)] = status
        return records
    if isinstance(raw, dict):
        for key, status in raw.items():
            # key 形如 "bcg:1"。
            parts = str(key).split(":")
            if len(parts) == 2:
                vaccine = parts[0]
                dose = _as_int(parts[1]) or 1
                records[(vaccine, dose)] = str(status)
        return records
    return records


def _as_int(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _str_or(v: Any, default: str) -> str:
    if v is None or v == "":
        return default
    return str(v)


__all__ = [
    "DUE_SOON_DAYS",
    "OVERDUE_BLUE_DAYS",
    "OVERDUE_YELLOW_DAYS",
    "UPCOMING_DAYS",
    "VaccineRuleModule",
]

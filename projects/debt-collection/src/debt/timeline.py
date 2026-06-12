# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-12 00:50:00 CST
"""① 诉讼时效计算与预警（F3, AC-3） ② 案件时间线聚合（ADR-006）。

诉讼时效（中国民法典第188条）：一般 3 年，自权利人知道或应当知道权利受损起算。
本模块做客观计算，关键日期由老板确认（防误算，RISK-7）。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from debt.models import Debt, Intel, Store, TimelineEvent

PRESCRIPTION_YEARS = 3   # 一般诉讼时效 3 年


def _parse(d: str) -> date | None:
    try:
        return datetime.strptime(d.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


@dataclass
class PrescriptionStatus:
    """诉讼时效状态。"""

    start_date: str           # 起算日（优先用最后催收日，否则约定还款日）
    deadline: str             # 时效届满日
    days_left: int            # 剩余天数（负数=已过）
    expired: bool
    level: str                # ok / warning(≤180天) / urgent(≤30天) / expired
    advice: str


def prescription_status(debt: Debt, today: date | None = None) -> PrescriptionStatus:
    """计算一笔债务的诉讼时效状态。

    起算日规则（简化）：最后催收/承诺日 > 约定还款日（最后催收会中断时效重新起算）。
    """
    today = today or date.today()
    start = _parse(debt.last_contact_date) or _parse(debt.due_date)
    if start is None:
        return PrescriptionStatus(
            start_date="", deadline="", days_left=0, expired=False, level="unknown",
            advice="缺少『约定还款日』或『最后催收日』，无法计算时效，请补全关键日期。",
        )
    deadline = date(start.year + PRESCRIPTION_YEARS, start.month, start.day) \
        if not (start.month == 2 and start.day == 29) \
        else date(start.year + PRESCRIPTION_YEARS, 3, 1)
    days_left = (deadline - today).days
    expired = days_left < 0
    if expired:
        level, advice = "expired", "⛔ 已过诉讼时效！可能丧失胜诉权，请立即咨询律师补救(如让对方书面确认债务以重启时效)。"
    elif days_left <= 30:
        level, advice = "urgent", "🔴 时效即将届满(≤30天)！立即采取中断措施：发律师函/起诉/让对方书面确认。"
    elif days_left <= 180:
        level, advice = "warning", "🟡 时效进入预警(≤180天)，建议尽快推进催收并保留中断证据。"
    else:
        level, advice = "ok", "🟢 时效充足，但仍建议定期催收并保留证据。"
    return PrescriptionStatus(
        start_date=start.isoformat(), deadline=deadline.isoformat(),
        days_left=days_left, expired=expired, level=level, advice=advice,
    )


def build_timeline(debt: Debt, intels: list[Intel]) -> list[TimelineEvent]:
    """把债务关键日期 + 情报聚合成按时间排序的案件时间线（ADR-006）。"""
    events: list[TimelineEvent] = []
    if debt.lend_date:
        events.append(TimelineEvent(debt.lend_date, "debt", f"借出/账期起算：{debt.amount}元"))
    if debt.due_date:
        events.append(TimelineEvent(debt.due_date, "debt", "约定还款日"))
    if debt.last_contact_date:
        events.append(TimelineEvent(debt.last_contact_date, "contact", "最后催收/对方承诺"))
    for it in intels:
        events.append(TimelineEvent(it.created_at or "", "intel",
                                    f"[{it.source}/{it.credibility.value}] {it.content}"))
    # 按日期排序（空日期排最后）
    events.sort(key=lambda e: e.when or "9999-99-99")
    return events

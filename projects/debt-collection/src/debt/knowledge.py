# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-12 01:30:00 CST
"""法务知识（knowledge-legal, ADR-002/006 防幻觉）。

V1：内置一组**核对过的核心法条要点**（讨债高频）+ 提供"法条引用必须回溯法规库"的接口。
理由：LLM 易编造法条，策略报告引用的法条必须来自可信来源(国家法规库)，不能 LLM 直出。
真机可扩展：从 flk.npc.gov.cn 取最新条文 / 本地维护各地执行口径。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LegalPoint:
    """一条核对过的法条要点。"""

    topic: str
    law: str            # 法律名称 + 条款
    summary: str        # 要点（人话）
    source_url: str = "https://flk.npc.gov.cn/"   # 回溯到国家法规库核对


# V1 内置核心法条要点（讨债高频；引用前应回溯 source 核对最新版本）
CORE_POINTS: dict[str, LegalPoint] = {
    "诉讼时效": LegalPoint(
        "诉讼时效", "《民法典》第188条",
        "向法院请求保护民事权利的诉讼时效一般为3年，自权利人知道或应当知道权利受损及义务人之日起算；"
        "最长不超过20年。", ),
    "时效中断": LegalPoint(
        "时效中断", "《民法典》第195条",
        "权利人提起诉讼、向义务人提出履行请求、义务人同意履行等，诉讼时效中断，从中断时重新起算。"
        "→ 保留催收记录/对方还款承诺可中断时效。", ),
    "支付令": LegalPoint(
        "支付令", "《民事诉讼法》督促程序",
        "债权债务关系明确、债权人未对待给付义务的，可申请支付令，比诉讼更快；对方15日内不异议即可申请执行。", ),
    "财产保全": LegalPoint(
        "财产保全", "《民事诉讼法》保全制度",
        "可在起诉前/诉讼中申请财产保全，冻结对方财产，防止其转移→提高执行到位率(应对老赖)。", ),
    "民间借贷利率": LegalPoint(
        "民间借贷利率", "民间借贷司法解释",
        "受法律保护的利率有上限(以 LPR 为基准的倍数)，超出部分不受保护；约定不明视为无息。", ),
    "失信与限高": LegalPoint(
        "失信与限高", "《民事诉讼法》+失信被执行人规定",
        "被执行人不履行的，可被纳入失信名单、限制高消费(限乘飞机高铁、限子女就读高收费私立学校等)，形成信用惩戒压力。", ),
}


def get_points(*topics: str) -> list[LegalPoint]:
    """按主题取法条要点；无主题则返回全部。"""
    if not topics:
        return list(CORE_POINTS.values())
    return [CORE_POINTS[t] for t in topics if t in CORE_POINTS]


def legal_context_for_strategy() -> str:
    """生成给策略 LLM 的"可信法条上下文"(防幻觉：让模型基于这些写，而非自己编)。"""
    lines = ["【可信法条要点（须基于此，勿编造法条）】"]
    for p in CORE_POINTS.values():
        lines.append(f"- {p.topic}（{p.law}）：{p.summary}")
    lines.append("（如需引用具体条文，请回溯 https://flk.npc.gov.cn/ 核对最新版本）")
    return "\n".join(lines)

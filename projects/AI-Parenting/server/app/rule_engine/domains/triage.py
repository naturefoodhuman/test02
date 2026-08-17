# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
#
# app/rule_engine/domains/triage.py —— 分诊规则域（APC-T021）。
# 依据：ARCHITECTURE_FINAL §10.2（分诊：红黄蓝阈值/危险信号/3 月龄以下直肠温 38°C 强红线）、
#       §13.2（mmWave 不单独触发红色医疗告警）、§14.1（告警等级）；
#       FINAL_PRD §11.9（红线：3 月龄及以下 ≥38°C 触发红色分诊，不优先给药）、
#       §11.10（医疗分诊 V1：风险等级/危险信号/就医建议，不做确诊/替代医生/自由开药）；
#       ENGINEERING_DESIGN §7.3；TASK_BACKLOG APC-T021。
# 设计：TriageRuleModule 实现 RuleModule Protocol（domain="triage"）。
#       体温阈值规则复用 kernel.evaluate_pack（规则包 YAML 驱动，首匹配），
#       叠加危险信号（danger_signals）与 mmWave 约束（单信号不得红色医疗告警）。
#       输出 Alert candidate：alert_level + danger_signals + advice + evidence。
# 边界：只产出分诊 verdict/alert_level/danger_signals/advice（架构 §10.2），
#       不做确诊、不替代医生、不自由开药、不出剂量（剂量在 medication 域）。
#       mmWave 单信号最多 orange（§13.2），不得 red 医疗告警。

"""分诊规则域（APC-T021）。

``TriageRuleModule`` 实现 ``RuleModule`` Protocol（``domain="triage"``）。

体温阈值由规则包 YAML 驱动（``kernel.evaluate_pack`` 首匹配），覆盖：
    - 3 月龄以下（``baby_age_days < 90``）≥38°C → 强红线 ``red``（PRD §11.9）。
    - 3 月龄以上 ≥39°C → 橙色 ``orange``。
    - 3 月龄以上 38~39°C → 黄色 ``yellow``。

叠加层（规则包外，本模块直接实现）：
    - **危险信号**（``variables.danger_signals``）：抽搐/呼吸困难/前囟膨隆/皮肤花纹/
      反应低下/持续呕吐/出血点等 → 无论体温如何，升级为 ``red`` 并附 danger_signals。
    - **mmWave 约束**（§13.2）：``variables.signal_source == "mmwave"`` 单信号不得产生
      红色医疗告警，最多降级为 ``orange``（辅助监测异常，请人工查看）。
    - **就医建议**：按 alert_level 产出 advice（立即就医 / 尽快就医 / 观察并咨询医生）。

输出 Alert candidate（``outputs``）：``alert_level`` + ``danger_signals`` + ``advice``。
``evidence`` 含 rule_id + policy_version + 文本，供审计追溯（§15.4）。
"""

from __future__ import annotations

from typing import Any

from ..domain.models import (
    EvidenceRef,
    RuleContext,
    RuleDomain,
    RuleInput,
    RulePack,
    RuleResult,
    Verdict,
)
from ..kernel import evaluate_pack

# 3 月龄阈值（天）：低于此且 ≥38°C 为强红线（PRD §11.9）。
RED_LINE_AGE_DAYS = 90
# mmWave 单信号最高告警等级（§13.2：不单独触发红色医疗告警）。
MMWAVE_MAX_LEVEL = "orange"

# 危险信号 → 红色分诊（PRD §11.10 危险信号清单，非穷尽，可经规则包扩展）。
_DANGER_SIGNAL_REASONS = {
    "convulsion": "抽搐",
    "breathing_difficulty": "呼吸困难",
    "bulging_fontanelle": "前囟膨隆",
    "mottled_skin": "皮肤花纹",
    "unresponsive": "反应低下",
    "persistent_vomiting": "持续呕吐",
    "bleeding_spots": "出血点",
    "cyanosis": "发绀",
}


class TriageRuleModule:
    """分诊规则模块（APC-T021，domain="triage"）。

    体温阈值由规则包 YAML 驱动（``evaluate_pack`` 首匹配），危险信号与 mmWave 约束
    由本模块叠加。规则包版本化（§13.2）；规则包加载失败时退化为仅危险信号 + mmWave 约束。
    """

    domain: RuleDomain = "triage"

    def __init__(self, pack: RulePack) -> None:
        self._pack = pack
        self._rule_version = f"{pack.policy_type}@{pack.version}"

    async def evaluate(self, input_: RuleInput, ctx: RuleContext) -> RuleResult:
        """跑分诊链路 → Alert candidate（alert_level + danger_signals + advice）。"""
        variables = input_.variables
        danger_signals = _collect_danger_signals(variables)
        signal_source = variables.get("signal_source")

        # 1. 体温阈值（规则包 YAML 驱动，首匹配）。
        base = evaluate_pack(self._pack, input_, ctx)
        alert_level = str(base.outputs.get("alert_level", "")) or "info"
        reason_code = base.reason_code
        evidence_text = base.evidence[0].text if base.evidence else ""

        # 2. 危险信号：任一命中 → 强制升级 red（无论体温）。
        if danger_signals:
            alert_level = "red"
            reason_code = "danger_signal_red"
            evidence_text = evidence_text or "危险信号命中，触发红色分诊（PRD §11.10）"

        # 3. mmWave 约束：单信号不得红色医疗告警，red → 降级 orange（§13.2）。
        if signal_source == "mmwave" and alert_level == "red":
            alert_level = MMWAVE_MAX_LEVEL
            reason_code = "mmwave_signal_capped"
            evidence_text = "mmWave 单信号不触发红色医疗告警，降级为橙色辅助提示（§13.2）"

        # 4. 就医建议（按 alert_level）。
        advice = _advice_for(alert_level)

        outputs: dict[str, Any] = {
            "alert_level": alert_level,
            "advice": advice,
        }
        if danger_signals:
            outputs["danger_signals"] = danger_signals

        return RuleResult(
            verdict=_verdict_for(alert_level),
            outputs=outputs,
            evidence=[
                EvidenceRef(
                    rule_id="triage",
                    policy_version=ctx.policy_version,
                    text=evidence_text,
                )
            ],
            rule_version=self._rule_version,
            reason_code=reason_code,
        )


# ---- 辅助 ----


def _collect_danger_signals(variables: dict[str, Any]) -> list[str]:
    """从 variables.danger_signals（list[str] 或逗号串）收集命中的危险信号。"""
    raw = variables.get("danger_signals")
    if raw is None:
        return []
    if isinstance(raw, str):
        items = [s.strip() for s in raw.split(",") if s.strip()]
    elif isinstance(raw, (list, tuple)):
        items = [str(s).strip() for s in raw if s]
    else:
        return []
    # 只保留已知危险信号（防注入未知 key 滥升红）。
    return [it for it in items if it in _DANGER_SIGNAL_REASONS]


def _verdict_for(level: str) -> Verdict:
    """alert_level → verdict（red=block，orange/yellow=warn，其余 info）。"""
    if level == "red":
        return "block"
    if level in ("orange", "yellow"):
        return "warn"
    return "info"


def _advice_for(level: str) -> str:
    """按 alert_level 产出就医建议（PRD §11.10：何时就医）。"""
    if level == "red":
        return "立即就医或联系儿科医生（红色分诊，不优先给药）"
    if level == "orange":
        return "24h 内联系医生评估"
    if level == "yellow":
        return "观察并咨询医生，注意体温变化"
    return "继续观察"


__all__ = [
    "MMWAVE_MAX_LEVEL",
    "RED_LINE_AGE_DAYS",
    "TriageRuleModule",
]

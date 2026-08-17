# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
#
# app/rule_engine/domains/medication.py —— 用药规则域（APC-T020）。
# 依据：ENGINEERING_DESIGN §7.4（用药安全：Rule Engine 为执行器，mg→ml→间隔→24h上限）；
#       ARCHITECTURE_FINAL §4.4、§10.2（RuleModule 唯一剂量裁决者）；
#       FINAL_PRD §11.11.2（必须输入）、§11.11.3（规则流程）、§11.11.4（硬性限制）；
#       TASK_BACKLOG APC-T020（未知体重不出剂量/未知浓度不出 ml/体重过旧/<6月龄布洛芬 block/
#       接近24h上限阻止重复/dose 只来自 RuleResult；golden 覆盖 allow/block/warn）。
# 设计：MedicationRuleModule 实现 RuleModule Protocol（domain="medication"）。
#       药物参数表从规则包 YAML 的 rules[].action.outputs 读取（每条 rule=一个药物，
#       conditions 匹配 variables.drug；outputs 存 mg_per_kg/min_age_months/interval_hours/
#       max_24h_mg_per_kg/max_single_dose_mg/concentration_mg_ml 默认值）。
#       校验链路（PRD §11.11.3）：选药→校验月龄→校验体重时效→确认浓度→检查禁忌→
#       计算 mg→换算 ml→检查间隔→检查 24h 上限。任一硬拦截→block/warn，dose 只在 allow 时产出。
#       占位参数（mg_per_kg=0 等）→ block（待医生确认，§0.5 安全关键，不凭空计算）。
# 边界：只有本 Module 产出 dose_mg/dose_ml（架构 §10.2）；LLM/copilots 不得计算。
#       药物数值参数为占位（source=TODO 待医生确认），不凭空编造医疗数值。

"""用药规则域（APC-T020）。

``MedicationRuleModule`` 实现 ``RuleModule`` Protocol（``domain="medication"``）。
药物参数表从规则包 YAML 的 ``rules[].action.outputs`` 读取（每条 rule = 一个药物，
``conditions`` 匹配 ``variables.drug``；``outputs`` 存 ``mg_per_kg``/``min_age_months``/
``interval_hours``/``max_24h_mg_per_kg``/``max_single_dose_mg``/``concentration_mg_ml``）。

校验链路（PRD §11.11.3）：选药 → 校验月龄 → 校验体重时效 → 确认浓度 → 检查禁忌 →
计算 mg → 换算 ml → 检查间隔 → 检查 24h 上限。任一硬拦截 → ``block``/``warn``，
``dose_mg``/``dose_ml`` 只在 ``allow`` 时产出（架构 §10.2：只有 RuleModule 可产出剂量）。

硬性限制（PRD §11.11.4）：
    - 未知体重 → block，不出剂量。
    - 未知浓度 → block，不出 ml。
    - 体重记录过旧（> ``weight_stale_days``）→ warn，要求更新。
    - 布洛芬 <6 月龄 → block（仅 ``doctor_override`` 模式 allow）。
    - 24h 已接近上限 → block，阻止重复给药。
    - 占位参数（``mg_per_kg=0``）→ block（待医生确认，安全关键不凭空计算）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..domain.models import EvidenceRef, RuleContext, RuleDomain, RuleInput, RulePack, RuleResult

# 体重记录过期阈值（天）：超过则 warn 要求更新（PRD §11.11.4 "体重记录过旧"）。
WEIGHT_STALE_DAYS = 7
# 24h 上限接近阈值：累计量 ≥ max_24h_mg 的 (1 - SAFETY_MARGIN) 即阻止重复。
SAFETY_MARGIN = 0.1  # 10% 安全余量


class MedicationRuleModule:
    """用药规则模块（APC-T020，domain="medication"）。

    药物参数表从规则包 YAML 加载（构造时），``evaluate`` 按输入 ``variables.drug``
    取参数跑校验链路。规则包版本化（§13.2）；参数占位（``mg_per_kg=0``）时 block，
    待医生确认后填入真实数值再激活新版本。
    """

    domain: RuleDomain = "medication"

    def __init__(self, pack: RulePack) -> None:
        self._pack = pack
        self._rule_version = f"{pack.policy_type}@{pack.version}"
        self._params: dict[str, dict[str, Any]] = {}
        for rule in pack.rules:
            # 每条 rule 的 conditions 匹配 variables.drug；取 outputs 作药物参数。
            drug = _extract_drug_match(rule.conditions)
            if drug is not None:
                self._params[drug] = dict(rule.action.outputs)
                self._params[drug]["evidence_text"] = rule.action.evidence_text

    async def evaluate(self, input_: RuleInput, ctx: RuleContext) -> RuleResult:
        """跑用药校验链路 → RuleResult（dose 只在 allow 时产出）。"""
        variables = input_.variables
        drug = variables.get("drug")
        if drug is None or drug not in self._params:
            return self._result("block", "unknown_drug", "未知药物，无法校验")

        params = self._params[drug]
        evidence_text = params.get("evidence_text", "")

        # 1. 未知体重 → block，不出剂量（PRD §11.11.4）。
        if input_.weight_kg is None or input_.weight_kg <= 0:
            return self._result("block", "unknown_weight", "未知体重，不出剂量", evidence_text)

        # 2. 体重记录过旧 → warn 要求更新（PRD §11.11.4）。
        weight_age_days = _as_int(variables.get("weight_age_days"))
        if weight_age_days is not None and weight_age_days > WEIGHT_STALE_DAYS:
            return self._result(
                "warn", "weight_stale", "体重记录过旧，请更新体重后再给药", evidence_text
            )

        # 3. 月龄校验 + 禁忌（<min_age_months → block，除非 doctor_override）。
        min_age_months = _as_int(params.get("min_age_months"))
        baby_age_days = input_.baby_age_days
        doctor_override = bool(variables.get("doctor_override"))
        if (
            min_age_months is not None
            and baby_age_days is not None
            and baby_age_days < min_age_months * 30
        ):
            if doctor_override:
                # 医生已明确要求模式：allow 但 warn 标注（PRD §11.11.4 布洛芬<6月龄）。
                return self._dose_result(
                    params,
                    input_,
                    "warn",
                    "doctor_override_under_min_age",
                    f"{drug} 低于最小月龄，医生已明确要求，请二次确认",
                    evidence_text,
                )
            return self._result(
                "block",
                "under_min_age",
                f"{drug} 低于最小月龄 {min_age_months} 月，默认锁定",
                evidence_text,
            )

        # 4. 占位参数检查（mg_per_kg=0 → 待医生确认，block）。放在体重/月龄校验之后，
        #    使各校验分支可独立测试；占位参数只在"本应计算 mg"时 block。
        mg_per_kg = _as_float(params.get("mg_per_kg"))
        if mg_per_kg is None or mg_per_kg <= 0:
            return self._result(
                "block", "params_pending", f"{drug} 参数待医生确认，不出剂量", evidence_text
            )

        # 5. 计算 mg（mg_per_kg × weight_kg，受 max_single_dose_mg 上限）。
        dose_mg = mg_per_kg * input_.weight_kg
        max_single = _as_float(params.get("max_single_dose_mg"))
        if max_single is not None and max_single > 0 and dose_mg > max_single:
            dose_mg = max_single

        # 6. 未知浓度 → block，不出 ml（PRD §11.11.4）。但 mg 已可输出（剂量已知，ml 待浓度）。
        concentration = _as_float(variables.get("concentration_mg_ml"))
        if concentration is None or concentration <= 0:
            return self._result(
                "block",
                "unknown_concentration",
                "未知浓度，不出 ml",
                evidence_text,
                outputs={"dose_mg": round(dose_mg, 2)},
            )

        # 7. 换算 ml。
        dose_ml = dose_mg / concentration

        # 8. 检查给药间隔（last_dose_at + interval_hours）。
        interval_hours = _as_float(params.get("interval_hours"))
        last_dose_at = variables.get("last_dose_at")
        now = (
            ctx.now or datetime.now(tz=last_dose_at.tzinfo)
            if isinstance(last_dose_at, datetime)
            else ctx.now
        )
        if (
            interval_hours is not None
            and interval_hours > 0
            and isinstance(last_dose_at, datetime)
            and now is not None
        ):
            elapsed_hours = (now - last_dose_at).total_seconds() / 3600.0
            if elapsed_hours < interval_hours:
                return self._result(
                    "block",
                    "interval_too_short",
                    f"距上次给药 {elapsed_hours:.1f}h < 间隔 {interval_hours}h，阻止重复",
                    evidence_text,
                    outputs={"dose_mg": round(dose_mg, 2), "dose_ml": round(dose_ml, 2)},
                )

        # 9. 检查 24h 上限（累计 24h_mg + 本次 dose_mg ≥ max_24h_mg × (1-SAFETY_MARGIN)）。
        max_24h_mg_per_kg = _as_float(params.get("max_24h_mg_per_kg"))
        given_24h_mg = _as_float(variables.get("given_24h_mg")) or 0.0
        if max_24h_mg_per_kg is not None and max_24h_mg_per_kg > 0:
            max_24h_mg = max_24h_mg_per_kg * input_.weight_kg
            if given_24h_mg + dose_mg >= max_24h_mg * (1 - SAFETY_MARGIN):
                return self._result(
                    "block",
                    "near_24h_limit",
                    f"24h 累计 {given_24h_mg:.1f}mg + 本次 {dose_mg:.1f}mg 接近上限 {max_24h_mg:.1f}mg，阻止重复",
                    evidence_text,
                    outputs={"dose_mg": round(dose_mg, 2), "dose_ml": round(dose_ml, 2)},
                )

        # 10. allow：产出 dose_mg + dose_ml。
        return self._dose_result(
            params,
            input_,
            "allow",
            "ok",
            f"{drug} 校验通过",
            evidence_text,
            dose_mg=dose_mg,
            dose_ml=dose_ml,
        )

    # ---- 辅助构造 RuleResult ----

    def _result(
        self,
        verdict: str,
        reason_code: str,
        message: str,
        evidence_text: str = "",
        outputs: dict[str, Any] | None = None,
    ) -> RuleResult:
        return RuleResult(
            verdict=verdict,  # type: ignore[arg-type]
            outputs=outputs or {},
            evidence=[
                EvidenceRef(
                    rule_id="medication",
                    policy_version=self._pack.version,
                    text=evidence_text or message,
                )
            ],
            rule_version=self._rule_version,
            reason_code=reason_code,
        )

    def _dose_result(
        self,
        params: dict[str, Any],
        input_: RuleInput,
        verdict: str,
        reason_code: str,
        message: str,
        evidence_text: str = "",
        dose_mg: float | None = None,
        dose_ml: float | None = None,
    ) -> RuleResult:
        outputs: dict[str, Any] = {}
        if dose_mg is not None:
            outputs["dose_mg"] = round(dose_mg, 2)
        if dose_ml is not None:
            outputs["dose_ml"] = round(dose_ml, 2)
        return RuleResult(
            verdict=verdict,  # type: ignore[arg-type]
            outputs=outputs,
            evidence=[
                EvidenceRef(
                    rule_id="medication",
                    policy_version=self._pack.version,
                    text=evidence_text or message,
                )
            ],
            rule_version=self._rule_version,
            reason_code=reason_code,
        )


# ---- 模块级辅助 ----


def _extract_drug_match(conditions: list) -> str | None:
    """从 rule.conditions 取 variables.drug 的 eq 匹配值（药物名）。

    期望 conditions 含一条 ``{op: eq, field: variables.drug, value: <name>}``。
    """
    for cond in conditions:
        if cond.op == "eq" and cond.field == "variables.drug":
            return str(cond.value)
    return None


def _as_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
        return f
    except (TypeError, ValueError):
        return None


def _as_int(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


__all__ = ["SAFETY_MARGIN", "WEIGHT_STALE_DAYS", "MedicationRuleModule"]

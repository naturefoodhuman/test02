# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/rule_engine/domain/models.py —— Rule Engine 领域模型（APC-T018）。
# 依据：ENGINEERING_DESIGN §5.3（RuleModule 唯一医疗/剂量/阈值裁决者）、§6、§13.2；
#       ARCHITECTURE_FINAL §10.2、§11.3；TASK_BACKLOG APC-T018。
# 设计：RuleResult（verdict/outputs/evidence/rule_version/reason_code）+ RuleInput/RuleContext/
#       RuleModule Protocol + EvidenceRef + Rule/RulePack YAML schema（Pydantic）。
#       规则包版本化，hash 可校验；YAML → Pydantic → 冻结策略。
# 边界：只有 RuleModule 可产出 dose/threshold/verdict（架构 §10.2）；LLM/copilots 不得计算。

"""Rule Engine 领域模型（APC-T018）。

架构（ENGINEERING_DESIGN §5.3 / §13.2）：
- ``RuleResult``：verdict（allow/block/warn/info）+ outputs（dose/threshold 等）+ evidence
  + rule_version + reason_code。只有 RuleModule 可产出。
- ``RuleModule`` Protocol：按 domain（medication/vaccine/growth/triage/thresholds）求值。
- ``RulePack``：YAML 规则包 schema（policy_type/region/version/effective_from/rules[]），
  版本化 + hash 校验；YAML → Pydantic → 冻结策略（§13.2）。
- ``EvidenceRef``：rule_id + policy_version + text，追溯证据来源。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

Verdict = Literal["allow", "block", "warn", "info"]
RuleDomain = Literal["medication", "vaccine", "growth", "triage", "thresholds"]


class EvidenceRef(BaseModel):
    """证据引用（追溯规则来源，架构 §5.3）。"""

    model_config = ConfigDict(frozen=True)

    rule_id: str = Field(description="规则 id（规则包内唯一）")
    policy_version: int = Field(description="EvidencePolicy 版本号")
    text: str = Field(description="证据文本（展示用）")


class RuleResult(BaseModel):
    """规则求值结果（架构 §5.3，唯一医疗/剂量/阈值裁决输出）。

    ``verdict``：allow/block/warn/info。
    ``outputs``：dose/threshold 等（e.g. {"dose_mg":60,"dose_ml":2.5}）。
    ``evidence``：证据引用列表（rule_id + policy_version + text）。
    ``rule_version``：规则包版本（hash 或 semver）。
    ``reason_code``：机读原因码（e.g. "weight_unknown"/"under_6mo_ibuprofen"）。
    """

    model_config = ConfigDict(frozen=True)

    verdict: Verdict
    outputs: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    rule_version: str
    reason_code: str


class RuleInput(BaseModel):
    """规则求值输入（领域数据 + 上下文变量）。

    ``baby_id``/``baby_age_days``/``weight_kg`` 等领域事实；``variables`` 自由变量
    （体温、24h 奶量等，由 State Engine 派生传入）。具体字段由各规则域扩展。
    """

    model_config = ConfigDict(extra="allow")

    baby_id: str | None = None
    baby_age_days: int | None = None
    weight_kg: float | None = None
    variables: dict[str, Any] = Field(default_factory=dict)


class RuleContext(BaseModel):
    """规则求值上下文（当前生效 EvidencePolicy 版本、区域等）。

    ``policy_version``：当前生效的 EvidencePolicy 版本（写入 RuleResult.evidence）。
    ``region``：区域（影响规则版本，e.g. "CN"）。
    """

    model_config = ConfigDict(extra="allow")

    policy_version: int
    region: str = "CN"
    now: datetime | None = None


@runtime_checkable
class RuleModule(Protocol):
    """规则模块协议（架构 §5.3，唯一医疗/剂量/阈值裁决者）。

    ``domain``：medication/vaccine/growth/triage/thresholds。
    ``evaluate``：求值输入 → RuleResult。只有 RuleModule 可产出 dose/threshold/verdict。
    """

    domain: RuleDomain

    async def evaluate(self, input_: RuleInput, ctx: RuleContext) -> RuleResult: ...


# ---- YAML 规则包 schema（§13.2）----


class RuleCondition(BaseModel):
    """规则条件（YAML schema）：算子 + 字段 + 阈值。

    ``op``：比较算子（eq/ne/lt/lte/gt/gte/in/not_in/range）。
    ``field``：输入字段路径（e.g. "weight_kg"/"variables.temperature_c"）。
    ``value``：阈值（标量或区间 [lo, hi]）。
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["eq", "ne", "lt", "lte", "gt", "gte", "in", "not_in", "range"]
    field: str
    value: Any


class RuleAction(BaseModel):
    """规则动作（YAML schema）：匹配时产出 verdict + outputs + reason_code。"""

    model_config = ConfigDict(extra="forbid")

    verdict: Verdict
    outputs: dict[str, Any] = Field(default_factory=dict)
    reason_code: str
    evidence_text: str = Field(default="", description="证据文本（展示用）")


class Rule(BaseModel):
    """单条规则（YAML schema）：条件 + 动作。

    ``rule_id``：规则包内唯一 id。
    ``conditions``：全部满足则匹配（AND）。
    ``action``：匹配时产出。
    """

    model_config = ConfigDict(extra="forbid")

    rule_id: str
    conditions: list[RuleCondition] = Field(default_factory=list)
    action: RuleAction


class RulePack(BaseModel):
    """规则包（YAML schema，§13.2）：版本化策略。

    ``policy_type``：策略类型（与 EvidencePolicy.policy_type 对齐）。
    ``region``：区域（e.g. "CN"）。
    ``version``：版本号（递增，架构 §18）。
    ``effective_from``：生效时间。
    ``source``：来源（e.g. "WHO/国家指南"）。
    ``rule_text``：规则文本（EvidencePolicy.rule_text）。
    ``display_text``：展示文本（EvidencePolicy.display_text）。
    ``rules``：规则列表。
    ``hash``：内容 hash（loader 计算，校验完整性）。
    """

    model_config = ConfigDict(extra="forbid")

    policy_type: str
    region: str = "CN"
    version: int
    effective_from: datetime
    source: str
    rule_text: str
    display_text: str
    rules: list[Rule]
    hash: str | None = None


__all__ = [
    "EvidenceRef",
    "Rule",
    "RuleAction",
    "RuleCondition",
    "RuleContext",
    "RuleDomain",
    "RuleInput",
    "RuleModule",
    "RulePack",
    "RuleResult",
    "Verdict",
]

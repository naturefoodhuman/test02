# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/rule_engine/__init__.py —— Rule Engine 包入口（APC-T018）。
# 导出领域模型、求值核心、注册表、加载器、EvidencePolicy 仓储供 orchestrator/copilots 复用。

"""Rule Engine 包入口（APC-T018）。

导出领域模型（``RuleResult`` / ``RuleInput`` / ``RuleContext`` / ``RuleModule``）、
求值核心（``evaluate_pack`` / ``match_rule``）、注册表（``RuleRegistry``）、
加载器（``load_pack`` / ``validate_dir``）、EvidencePolicy 仓储。
具体规则域（medication/vaccine/growth/triage/thresholds）在 APC-T020~T023 接入。
"""

from .domain.models import (
    EvidenceRef,
    Rule,
    RuleAction,
    RuleCondition,
    RuleContext,
    RuleDomain,
    RuleInput,
    RuleModule,
    RulePack,
    RuleResult,
    Verdict,
)
from .evidence_repo import EvidencePolicyRepository, SqlAlchemyEvidencePolicyRepository
from .kernel import evaluate_pack, match_rule
from .loader import load_pack, validate_dir
from .registry import RuleRegistry

__all__ = [
    "EvidencePolicyRepository",
    "EvidenceRef",
    "Rule",
    "RuleAction",
    "RuleCondition",
    "RuleContext",
    "RuleDomain",
    "RuleInput",
    "RuleModule",
    "RulePack",
    "RuleRegistry",
    "RuleResult",
    "SqlAlchemyEvidencePolicyRepository",
    "Verdict",
    "evaluate_pack",
    "load_pack",
    "match_rule",
    "validate_dir",
]

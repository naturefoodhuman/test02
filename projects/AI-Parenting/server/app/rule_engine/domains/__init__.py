# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
#
# app/rule_engine/domains/__init__.py —— 规则域模块包入口（APC-T020+）。
# 各规则域（medication/triage/vaccine/growth/thresholds）在此目录实现 RuleModule，
# 启动期注册到 RuleRegistry（main.py），不改内核（开闭原则，架构 §13.5）。

"""规则域模块包入口（APC-T020+）。

各规则域（``medication``/``triage``/``vaccine``/``growth``/``thresholds``）在此目录
实现 ``RuleModule``，启动期注册到 ``RuleRegistry``（``main.py``），不改内核
（开闭原则，架构 §13.5）。新增域 = 实现模块 + 规则包 YAML + register。
"""

from .growth import GrowthRuleModule
from .medication import MedicationRuleModule
from .thresholds import ThresholdRuleModule
from .triage import TriageRuleModule
from .vaccine import VaccineRuleModule

__all__ = [
    "GrowthRuleModule",
    "MedicationRuleModule",
    "ThresholdRuleModule",
    "TriageRuleModule",
    "VaccineRuleModule",
]

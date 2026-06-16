# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-16 21:25:00
"""DataPrivacyGate: 策略文件驱动的数据出境门控

职责：
- 读取 privacy_policy.yaml
- 执行人类定义的数据出境策略（不是代码决定策略）
- 在数据发送到外部端点前进行拦截/脱敏/人工确认

**SSOT 引用（必须保持一致）**:
- 架构决策：docs/adr/ADR-003-data-privacy-gate-and-policy-file.md （策略文件驱动 + human_approve / local_only / mask 规则）
- 策略文件：config/privacy_policy.yaml （A 文件类，人类拥有）
- 使用位置：debt/cli.py (cmd_review), graph/nodes/ (privacy check), forge eval
- 核心原则：永远不让代码决定隐私策略，策略由 config/privacy_policy.yaml 人类定义并版本控制

修改本文件必须：
1. 更新头部时间戳
2. 同步更新 docs/ARCHITECTURE.md
3. 如涉及新策略类型或重大门控逻辑变更 → 创建 superseding ADR（绝不改历史 ADR-003）
4. 更新 CHANGELOG.md + 必要时运行治理检查
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from peer_review.config import load_privacy_policy_config
from peer_review.config.schemas import PrivacyPolicyConfig


class GateDecisionType(str, Enum):
    APPROVED = "approved"
    BLOCKED = "blocked"
    MASKED = "masked"
    REQUIRES_HUMAN = "requires_human"


@dataclass
class GateDecision:
    field: str
    decision: GateDecisionType
    masked_value: str | None = None
    reason: str = ""


@dataclass
class EgressCheckResult:
    """一批字段的出境检查结果"""

    allowed: bool = False
    decisions: list[GateDecision] = field(default_factory=list)
    requires_human_fields: list[str] = field(default_factory=list)
    blocked_fields: list[str] = field(default_factory=list)
    preview: dict[str, str] = field(default_factory=dict)


class DataPrivacyGate:
    """数据出境策略执行器"""

    def __init__(self, policy_path: Path | None = None):
        if policy_path is None:
            policy_path = self._find_default_policy_path()
        self.policy: PrivacyPolicyConfig = load_privacy_policy_config(policy_path)

    @staticmethod
    def _find_default_policy_path() -> Path:
        """向上查找项目根目录，定位 config/privacy_policy.yaml"""
        cwd = Path.cwd()
        for parent in [cwd] + list(cwd.parents):
            candidate = parent / "config" / "privacy_policy.yaml"
            if candidate.exists():
                return candidate
        # 兜底：返回当前目录下的相对路径（可能不存在，后续会抛出清晰错误）
        return Path("config/privacy_policy.yaml")

    def check(self, data: dict[str, Any], target_endpoint: str) -> EgressCheckResult:
        """检查数据是否可以发送到目标端点

        Args:
            data: 字段名 -> 字段值 映射
            target_endpoint: 目标端点名 (如 chinese_api, local_model)

        Returns:
            EgressCheckResult 包含是否允许、需人工确认字段、被阻断字段
        """
        endpoint_cfg = self.policy.endpoints.get(target_endpoint)
        if endpoint_cfg is None:
            # 未知端点默认阻断（最保守）
            return EgressCheckResult(
                allowed=False,
                blocked_fields=list(data.keys()),
                decisions=[
                    GateDecision(
                        field=k,
                        decision=GateDecisionType.BLOCKED,
                        reason=f"未知目标端点 '{target_endpoint}'",
                    )
                    for k in data
                ],
            )

        allowed_policies = set(endpoint_cfg.allowed_policies or [])
        requires_human_for = set(endpoint_cfg.requires_human_for or [])

        result = EgressCheckResult()

        for field_name, value in data.items():
            field_policy = self.policy.fields.get(field_name)
            if field_policy is None:
                # 未定义字段默认 human_approve（最保守）
                result.decisions.append(
                    GateDecision(
                        field=field_name,
                        decision=GateDecisionType.REQUIRES_HUMAN,
                        reason="字段未在隐私策略中定义",
                    )
                )
                result.requires_human_fields.append(field_name)
                result.preview[field_name] = str(value)
                continue

            policy = field_policy.policy
            display = field_policy.label or field_name

            if policy == "local_only":
                if target_endpoint != "local_model":
                    result.decisions.append(
                        GateDecision(
                            field=field_name,
                            decision=GateDecisionType.BLOCKED,
                            reason=f"{display} 策略为 local_only，不允许发送至 {target_endpoint}",
                        )
                    )
                    result.blocked_fields.append(field_name)
                else:
                    result.decisions.append(
                        GateDecision(
                            field=field_name,
                            decision=GateDecisionType.APPROVED,
                            reason="本地模型，允许",
                        )
                    )
                result.preview[field_name] = str(value)

            elif policy == "mask_then_allow":
                masked = self._apply_mask(value, field_policy.mask_rule)
                result.decisions.append(
                    GateDecision(
                        field=field_name,
                        decision=GateDecisionType.MASKED,
                        masked_value=masked,
                        reason=f"{display} 已脱敏 ({field_policy.mask_rule})",
                    )
                )
                result.preview[field_name] = masked

            elif policy == "human_approve":
                result.decisions.append(
                    GateDecision(
                        field=field_name,
                        decision=GateDecisionType.REQUIRES_HUMAN,
                        reason=f"{display} 需要人工确认",
                    )
                )
                result.requires_human_fields.append(field_name)
                result.preview[field_name] = str(value)

            elif policy == "allow":
                result.decisions.append(
                    GateDecision(
                        field=field_name,
                        decision=GateDecisionType.APPROVED,
                        reason=f"{display} 允许出境",
                    )
                )
                result.preview[field_name] = str(value)

        # 聚合判定：无阻断且无需人工确认则允许
        result.allowed = not result.blocked_fields and not result.requires_human_fields
        return result

    @staticmethod
    def request_human_approval(
        fields: list[str], preview: dict[str, str], endpoint_name: str
    ) -> bool:
        """人工审核门：必须显式输入 'yes' 才通过"""
        print("\n⚠️  [数据出境审核]")
        print(f"以下字段将发送到外部端点：{endpoint_name}")
        for field in fields:
            print(f"  • {field}：{preview.get(field, '(已脱敏)')}")
        print()
        response = input("确认发送？请输入 yes 确认，其他任意键取消：").strip().lower()
        return response == "yes"

    @staticmethod
    def _apply_mask(value: Any, rule: str | None) -> str:
        """简易脱敏实现（仅字符串处理）"""
        s = str(value)
        if rule is None:
            return "[MASKED]"
        if rule == "remove_personal_identifiers":
            # 仅演示：姓名替换为代称，真实实现应接入 NLP 或规则库
            return "[已脱敏：去除个人标识符]"
        if rule == "round_to_nearest_10000":
            try:
                num = float(s)
                return f"约 {round(num / 10000)} 万元"
            except ValueError:
                return s
        if rule == "keep_first_6_last_4":
            if len(s) >= 10:
                return f"{s[:6]}****{s[-4:]}"
            return "****"
        if rule == "keep_first_3_last_4":
            if len(s) >= 7:
                return f"{s[:3]}****{s[-4:]}"
            return "****"
        return "[MASKED]"

# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-12 00:50:00 CST
"""合规自检（F6, AC-4, ADR-006 护栏）。

目的：扫描策略文本/施压建议，拦截**违法**内容——这是讨债项目的红线守门人。
基于第一轮调研的 8 类入刑催收行为 + 非法获取个人信息。
区分：依法向任职单位反映真实欠债=正当维权(放行)；捏造/威胁/骚扰无关第三人=违法(拦截)。
"""
from __future__ import annotations

from dataclasses import dataclass, field


# 违法/高危关键词（命中即告警）——覆盖暴力/软暴力/非法查信息/骚扰第三人
ILLEGAL_PATTERNS: dict[str, str] = {
    # 暴力/软暴力
    "威胁": "涉嫌恐吓威胁(可构成寻衅滋事/催收非法债务罪)",
    "恐吓": "涉嫌恐吓威胁",
    "辱骂": "涉嫌侮辱(软暴力)",
    "殴打": "涉嫌人身伤害",
    "拘禁": "涉嫌非法拘禁",
    "蹲守": "涉嫌软暴力(跟踪蹲守)",
    "堵门": "涉嫌软暴力(滋扰)",
    "呼死你": "涉嫌电话轰炸(软暴力)",
    "电话轰炸": "涉嫌持续骚扰(软暴力)",
    "爆通讯录": "涉嫌侵犯公民个人信息+骚扰第三人",
    "群发": "向无关第三人散布欠款信息涉嫌违法",
    "泼漆": "涉嫌寻衅滋事",
    "喷漆": "涉嫌寻衅滋事",
    "拉横幅": "涉嫌羞辱式催收(寻衅滋事)",
    "冒充": "涉嫌招摇撞骗(冒充公职)",
    # 非法获取个人信息
    "查银行流水": "个人无权查他人流水，涉嫌侵犯公民个人信息罪",
    "查开房": "涉嫌非法获取个人信息",
    "定位": "未经授权定位涉嫌侵犯个人信息/隐私",
    "私家侦探": "涉嫌非法获取个人信息",
    "人肉": "涉嫌侵犯公民个人信息",
    # 骚扰第三人/未成年
    "骚扰家人": "禁止骚扰无关第三人",
    "影响子女上学": "涉嫌以虚假信息恐吓",
}

# 需人工注意但不一定违法（提示复核）
CAUTION_PATTERNS: dict[str, str] = {
    "联系第三方": "向第三方透露债务信息有边界，仅限债务人/担保人，且不得透露金额/逾期(注意合规)",
    "单位": "向任职单位反映需依法依规、只陈述真实事实，不得捏造/骚扰(注意分寸)",
    "上级": "向上级反映需基于真实欠债事实、正当维权，不得威胁恐吓",
    "曝光": "公开曝光需谨慎，不得侮辱诽谤/泄露隐私",
}


@dataclass
class ComplianceResult:
    """合规检查结果。"""

    passed: bool
    violations: list[str] = field(default_factory=list)   # 命中的违法项
    cautions: list[str] = field(default_factory=list)     # 需注意项

    def report(self) -> str:
        if self.passed and not self.cautions:
            return "✅ 合规检查通过：未发现违法或需注意内容。"
        lines = []
        if self.violations:
            lines.append("⛔ 发现违法/高危内容（必须删除/改写）：")
            lines += [f"  - {v}" for v in self.violations]
        if self.cautions:
            lines.append("⚠️ 需人工注意（合规边界）：")
            lines += [f"  - {c}" for c in self.cautions]
        return "\n".join(lines)


def check_text(text: str) -> ComplianceResult:
    """扫描一段文本的合规性。

    Args:
        text: 待检文本（策略建议/话术/筹码描述）。

    Returns:
        ComplianceResult；有 violations 则 passed=False。
    """
    t = text or ""
    violations = [f"命中『{k}』：{v}" for k, v in ILLEGAL_PATTERNS.items() if k in t]
    cautions = [f"涉及『{k}』：{v}" for k, v in CAUTION_PATTERNS.items() if k in t]
    return ComplianceResult(passed=len(violations) == 0, violations=violations, cautions=cautions)

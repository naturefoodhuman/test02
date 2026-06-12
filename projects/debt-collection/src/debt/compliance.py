# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建/修改时间（北京时间，精确到秒）：2026-06-12 16:00:00 CST
"""合规自检 v2（红线守门人，第21轮重构）。

第一版缺陷（老板真机发现）：纯关键词匹配 → 把"严禁威胁恐吓"误判为违规（假阳性）。
v2 改进：
  ① 否定语境识别：关键词前若有"严禁/绝不/不得/禁止/不要/避免/杜绝/勿"等否定词 → 不算违规。
  ② 严重度分级：明确违法指令=block(拦截)；边界/需注意=warn(不拦但提示)。
  ③ 结构化整改反馈：不合规时给出"问题句+原因+改写建议"，可回传 LLM 递归整改直至合规。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# 否定/禁止前缀（出现在违规词附近且语义为"禁止做X" → 合法，不算违规）
_NEGATION = ["严禁", "禁止", "绝不", "不得", "不要", "勿", "避免", "杜绝", "不可", "切勿",
             "不能", "拒绝", "反对", "并非", "而非", "不应", "非法", "违法"]
# 这些词出现时，若同句/邻近有否定前缀，视为"在强调不要这么做" → 放行
_NEG_WINDOW = 18   # 在违规词前 N 个字符内找否定词


@dataclass
class Finding:
    """一条合规发现。"""

    severity: str       # block(拦截) / warn(注意)
    keyword: str
    reason: str
    snippet: str        # 命中的上下文片段（便于定位与回传整改）
    suggestion: str     # 改写建议


# 明确违法/高危词 → block（但需排除否定语境）
ILLEGAL: dict[str, str] = {
    "爆通讯录": "侵犯公民个人信息+骚扰无关第三人",
    "呼死你": "电话轰炸(软暴力)",
    "电话轰炸": "持续骚扰(软暴力)",
    "查银行流水": "个人无权查他人流水，涉嫌侵犯公民个人信息罪",
    "查开房": "非法获取个人信息",
    "私家侦探": "非法获取个人信息",
    "人肉": "侵犯公民个人信息",
    "殴打": "人身伤害",
    "拘禁": "非法拘禁",
    "蹲守": "软暴力(跟踪蹲守)",
    "堵门": "软暴力(滋扰)",
    "泼漆": "寻衅滋事",
    "喷漆": "寻衅滋事",
    "拉横幅": "羞辱式催收(寻衅滋事)",
    "冒充公职": "招摇撞骗",
    "冒充警察": "招摇撞骗(冒充警察从重)",
}
# 高危动词类（威胁/恐吓/骚扰）——更需否定语境判断
ILLEGAL_VERBS: dict[str, str] = {
    "威胁": "恐吓威胁(可构成寻衅滋事/催收非法债务罪)",
    "恐吓": "恐吓威胁",
    "辱骂": "侮辱(软暴力)",
    "骚扰": "骚扰",
}
# 需注意（边界，warn 不拦）
CAUTION: dict[str, str] = {
    "联系第三方": "向第三方透露债务信息有边界，仅限债务人/担保人，且不得透露金额/逾期",
    "单位": "向任职单位反映需依法依规、只陈述真实事实，不得捏造/骚扰",
    "上级": "向上级反映需基于真实欠债事实、正当维权，不得威胁恐吓",
    "曝光": "公开曝光需谨慎，不得侮辱诽谤/泄露隐私",
    "组织反映": "向组织反映限于客观事实，不可作为敲诈筹码",
}


@dataclass
class ComplianceResult:
    """合规检查结果。"""

    passed: bool
    findings: list[Finding] = field(default_factory=list)

    @property
    def blocks(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "block"]

    @property
    def warns(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "warn"]

    def report(self) -> str:
        if self.passed and not self.warns:
            return "✅ 合规检查通过：未发现违法或需注意内容。"
        lines: list[str] = []
        if self.blocks:
            lines.append("⛔ 发现违法/高危内容（必须删除/改写）：")
            for f in self.blocks:
                lines.append(f"  - 『{f.keyword}』{f.reason}｜片段：…{f.snippet}…｜建议：{f.suggestion}")
        if self.warns:
            lines.append("⚠️ 需人工注意（合规边界）：")
            for f in self.warns:
                lines.append(f"  - 『{f.keyword}』{f.reason}")
        return "\n".join(lines)

    def fix_instruction(self) -> str:
        """生成可回传 LLM 的整改指令（递归重生成用，老板第21轮需求）。"""
        if not self.blocks:
            return ""
        items = []
        for f in self.blocks:
            items.append(f"- 删除或合法改写涉及『{f.keyword}』的内容（原因：{f.reason}）。"
                         f"片段：“…{f.snippet}…”。{f.suggestion}")
        return ("你上一版策略中存在以下【违法/高危】表述，请逐条整改后重新输出完整报告，"
                "其余合法内容保持质量：\n" + "\n".join(items) +
                "\n注意：如本就是『严禁/不得』等否定式表述，请保留；只改真正建议实施违法行为的部分。")


def _has_negation_before(text: str, pos: int) -> bool:
    """命中词位置前 _NEG_WINDOW 字符内是否有否定前缀。"""
    start = max(0, pos - _NEG_WINDOW)
    window = text[start:pos]
    return any(neg in window for neg in _NEGATION)


def _snippet(text: str, pos: int, length: int) -> str:
    s = max(0, pos - 12)
    e = min(len(text), pos + length + 12)
    return text[s:e].replace("\n", " ")


def _scan(text: str, table: dict[str, str], severity: str,
          *, skip_negated: bool) -> list[Finding]:
    findings: list[Finding] = []
    for kw, reason in table.items():
        for m in re.finditer(re.escape(kw), text):
            pos = m.start()
            # 否定语境（如"严禁威胁"）→ 合法，跳过
            if skip_negated and _has_negation_before(text, pos):
                continue
            findings.append(Finding(
                severity=severity, keyword=kw, reason=reason,
                snippet=_snippet(text, pos, len(kw)),
                suggestion="改为合法手段(如依法协商/律师函/诉讼保全)，或以『不得/严禁』方式表述边界。",
            ))
            break  # 同一关键词只报一次
    return findings


def check_text(text: str) -> ComplianceResult:
    """扫描文本合规性（v2：否定语境感知 + 分级 + 结构化反馈）。

    Args:
        text: 待检文本。

    Returns:
        ComplianceResult；有 block 级 finding 则 passed=False。
    """
    t = text or ""
    findings: list[Finding] = []
    # 明确违法词 + 高危动词：都做否定语境排除
    findings += _scan(t, ILLEGAL, "block", skip_negated=True)
    findings += _scan(t, ILLEGAL_VERBS, "block", skip_negated=True)
    # 边界词：warn（不拦）
    findings += _scan(t, CAUTION, "warn", skip_negated=False)
    passed = not any(f.severity == "block" for f in findings)
    return ComplianceResult(passed=passed, findings=findings)

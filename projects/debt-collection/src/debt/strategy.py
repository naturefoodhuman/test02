# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-12 01:30:00 CST
"""策略生成 + 动态重算 + 合法筹码识别（F5, ADR-002/004/006）。

流程：汇总(债务+时效+情报+法条) → 调 LLM(GLM优先)生成策略 → compliance 自检过滤 → 输出报告。
LLM 不可用时 → 离线模板兜底(基于规则给出结构化建议)，保证始终有可用产出。
所有产出过 compliance，确保"施压"建议合法。
"""
from __future__ import annotations

from dataclasses import dataclass

from debt import integrations  # noqa: F401  # 副作用：把工厂遥测/能力 path 注入
from debt import knowledge
from debt.compliance import check_text
from debt.llm_client import LLMConfig, available, chat
from debt.models import Debt, Intel
from debt.timeline import prescription_status

STRATEGY_SYSTEM = (
    "你是一位精通中国大陆债务追讨的资深律师助理。你的目标是帮债权人【合法、高效】把钱要回来。"
    "硬约束：①只给合法手段，绝不建议暴力/软暴力/骚扰无关第三人/非法查个人信息/冒充公职；"
    "②向债务人任职单位/上级反映真实欠债属正当维权，但不得捏造、不得威胁恐吓；"
    "③核心是实际讨回率与可执行性，不要给脱离国内执行实际的纸面方案；"
    "④引用法条须基于给定的『可信法条要点』，不得编造；⑤输出中文。"
)


@dataclass
class StrategyReport:
    """策略报告。"""

    debt_id: int | None
    debtor_name: str
    body: str                       # 报告正文
    model_used: str                 # GLM / local / offline-template
    compliance_passed: bool
    compliance_note: str = ""
    update_reason: str = ""         # 动态重算时：因哪条情报触发


def _facts_block(debt: Debt, intels: list[Intel]) -> str:
    st = prescription_status(debt)
    lines = [
        f"债务人：{debt.debtor_name}（{debt.debtor_region or '地域未填'}）",
        f"债务性质：{debt.nature.value}；本金 {debt.amount} 元，已还 {debt.repaid}，未还 {debt.outstanding}",
        f"当前阶段：{debt.stage.value}",
        f"诉讼时效：{st.level}（届满 {st.deadline or '未知'}，剩余 {st.days_left} 天）— {st.advice}",
        f"证据清单：{', '.join(debt.evidence) or '（无，需补全）'}",
    ]
    if intels:
        lines.append("已知情报：")
        for it in intels:
            lines.append(f"  - [{it.source}/{it.credibility.value}] {it.content}")
    return "\n".join(lines)


def _offline_template(debt: Debt, intels: list[Intel]) -> str:
    """LLM 不可用时的规则兜底报告（保证始终有结构化产出）。"""
    st = prescription_status(debt)
    parts = [
        f"# 讨债策略报告（离线模板）：{debt.debtor_name}",
        "",
        "## 1. 证据体检",
        f"- 当前证据：{', '.join(debt.evidence) or '不足，请尽快补全借条/转账记录/聊天记录'}",
        "## 2. 诉讼时效",
        f"- {st.advice}（届满 {st.deadline or '未知'}）",
        "## 3. 执行可行性预判",
        "- 先查对方是否失信/有无可执行财产（用取数清单）；若可能转移财产，考虑诉前财产保全。",
        "## 4. 合法博弈筹码",
    ]
    for it in intels:
        if it.affects_strategy:
            parts.append(f"- 据情报『{it.content}』：可考虑合法施压途径（须经合规校验，不得越界）。")
    if not any(it.affects_strategy for it in intels):
        parts.append("- 暂无影响策略的新情报。")
    parts += [
        "## 5. 讨债阶梯",
        "- 协商 → 律师函 → 支付令 → 起诉 → 执行（按回款概率与成本择优，优先非诉/保全）。",
        "## 6. 合法取数清单",
        "- 见 acquisition 生成的官方渠道待查清单。",
        "## 免责声明",
        "- 本报告为辅助参考，重大决策请咨询执业律师。",
    ]
    return "\n".join(parts)


def generate_report(debt: Debt, intels: list[Intel] | None = None,
                    *, cfg: LLMConfig | None = None, update_reason: str = "") -> StrategyReport:
    """生成策略报告（三级路由：GLM/在线 -> 本地主力 -> 离线模板），并过合规自检。

    三级路由逻辑（老板第24轮明确）：
    1. 尝试在线模型 (cloud/glm-primary)；
    2. 若不可用或失败，尝试本地主力模型 (local/primary)；
    3. 若本地也故障，降级至离线模板 (offline-template)。
    """
    intels = intels or []
    facts = _facts_block(debt, intels)
    legal = knowledge.legal_context_for_strategy()

    prompt = (
        f"{legal}\n\n【案件事实】\n{facts}\n\n"
        "请输出讨债策略报告，固定包含：1证据体检 2诉讼时效 3执行可行性预判(最重要,反老赖执行难) "
        "4合法博弈筹码(基于情报,须合法) 5讨债阶梯(协商→律师函→支付令→起诉→执行,标回款概率) "
        "6合法取数清单 7话术/文书要点(标注建议律师复核) 8免责声明。"
        + (f"\n【本次为动态更新，因新情报：{update_reason}，请重点说明策略调整】" if update_reason else "")
    )

    body: str | None = None
    model_used: str = "unknown"

    # 第一级：在线模型 (GLM)
    online_cfg = cfg or LLMConfig(model="cloud/glm-primary")
    if available(online_cfg):
        body, model_used = _generate_with_recheck(prompt, online_cfg, max_rounds=3)
    
    # 第二级：本地主力（若第一级失败或不可用）
    if not body or model_used == "offline-fallback":
        local_cfg = LLMConfig(model="local/primary")
        if available(local_cfg):
            body, model_used = _generate_with_recheck(prompt, local_cfg, max_rounds=3)

    # 第三级：离线模板（若前两级均失败）
    if not body or model_used == "offline-fallback":
        body = _offline_template(debt, intels)
        model_used = "offline-template"

    # 最终合规自检（红线守门人）
    cr = check_text(body)
    return StrategyReport(
        debt_id=debt.id, debtor_name=debt.debtor_name, body=body, model_used=model_used,
        compliance_passed=cr.passed, compliance_note=cr.report(), update_reason=update_reason,
    )


def _generate_with_recheck(prompt: str, cfg: LLMConfig, *, max_rounds: int = 3) -> tuple[str, str]:
    """生成 + 合规递归整改：不合规则把结构化整改指令回传 LLM 重生成，直至合规或达上限。

    Returns: (报告正文, 模型标识)
    """
    # 带遥测计时（终端实时计时器 + 落盘事件）
    try:
        from llm_telemetry.telemetry import track  # 工厂遥测（路径由 integrations 注入）
    except Exception:  # noqa: BLE001
        track = None  # 遥测不可用不阻塞

    cur_prompt = prompt
    last = ""
    for rnd in range(1, max_rounds + 1):
        event = f"strategy_report(r{rnd})"
        if track:
            with track(event, cfg.model, project="debt-collection", phase="BUILD",
                       prompt_chars=len(cur_prompt)) as t:
                out = chat(cur_prompt, system=STRATEGY_SYSTEM, cfg=cfg)
                t["output_chars"] = len(out or "")
                t["ok"] = bool(out)
        else:
            out = chat(cur_prompt, system=STRATEGY_SYSTEM, cfg=cfg)
        if not out:
            return (last or ""), (cfg.model if last else "offline-fallback")
        last = out
        cr = check_text(out)
        if cr.passed:
            return out, cfg.model
        # 不合规 → 把整改指令拼回，重生成
        fix = cr.fix_instruction()
        if not fix:
            return out, cfg.model
        cur_prompt = (prompt + "\n\n【合规整改要求（第" + str(rnd) + "轮未通过）】\n" + fix)
    # 达上限仍不合规：返回最后一版（上层会标注未通过，并附整改理由）
    return last, cfg.model

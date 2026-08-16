# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
"""RuleRegistry 单元测试（APC-T018）。

覆盖 register/get/domains/evaluate/未注册 KeyError。用 Fake RuleModule 替身。
asyncio_mode=auto。
"""

from __future__ import annotations

import pytest

from server.app.rule_engine.domain.models import RuleContext, RuleDomain, RuleInput, RuleResult
from server.app.rule_engine.registry import RuleRegistry


class FakeRuleModule:
    """测试用 RuleModule 替身：固定返回 RuleResult。"""

    def __init__(self, domain: RuleDomain, result: RuleResult) -> None:
        self.domain = domain
        self._result = result
        self.calls: list[tuple[RuleInput, RuleContext]] = []

    async def evaluate(self, input_: RuleInput, ctx: RuleContext) -> RuleResult:
        self.calls.append((input_, ctx))
        return self._result


def _result(verdict: str = "info", *, reason_code: str = "rc") -> RuleResult:
    return RuleResult(
        verdict=verdict, outputs={}, evidence=[], rule_version="t@1", reason_code=reason_code
    )  # type: ignore[arg-type]


def test_register_and_get():
    reg = RuleRegistry()
    mod = FakeRuleModule("medication", _result("block"))
    reg.register(mod)
    assert reg.get("medication") is mod


def test_get_unregistered_raises_keyerror():
    reg = RuleRegistry()
    with pytest.raises(KeyError, match="no RuleModule registered for domain=medication"):
        reg.get("medication")


def test_domains_lists_sorted():
    reg = RuleRegistry()
    reg.register(FakeRuleModule("vaccine", _result()))
    reg.register(FakeRuleModule("medication", _result()))
    assert reg.domains() == ["medication", "vaccine"]


def test_register_overwrites():
    reg = RuleRegistry()
    m1 = FakeRuleModule("medication", _result("block"))
    m2 = FakeRuleModule("medication", _result("warn"))
    reg.register(m1)
    reg.register(m2)
    assert reg.get("medication") is m2


async def test_evaluate_dispatches_to_module():
    reg = RuleRegistry()
    mod = FakeRuleModule("medication", _result("block", reason_code="under_6mo"))
    reg.register(mod)
    inp = RuleInput(baby_age_days=30)
    ctx = RuleContext(policy_version=1)
    r = await reg.evaluate("medication", inp, ctx)
    assert r.verdict == "block"
    assert r.reason_code == "under_6mo"
    assert mod.calls == [(inp, ctx)]


async def test_evaluate_unregistered_propagates_keyerror():
    reg = RuleRegistry()
    with pytest.raises(KeyError):
        await reg.evaluate("growth", RuleInput(), RuleContext(policy_version=1))

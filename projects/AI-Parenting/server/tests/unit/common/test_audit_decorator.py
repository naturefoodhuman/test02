# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""@audit 装饰器单元测试（APC-T006 测试要求：Unit decorator 捕获 before/after）。

用 AuditService 替身（记录 append 调用）验证：
    - before/after 快照正确捕获并写入 audit_log。
    - AuditResult 显式 before/after/rule_version/llm_call_id 透传。
    - actor 从 logger contextvars 取（user_id 优先）。
    - 资源模板 {kwarg} 占位填充。
    - 审计写入失败 → UpstreamUnavailable，mutating 操作不得静默成功。
    - 缺 audit 参数 → TypeError（防误用）。
"""

from __future__ import annotations

from typing import Any

import pytest

from server.app.common.audit_decorator import AuditResult, audit
from server.app.common.errors import UpstreamUnavailable
from server.app.observability.audit import AuditService
from server.app.observability.logger import bind_context, clear_context


class FakeAuditService(AuditService):
    """AuditService 替身：记录 append 调用，可选注入异常。

    模拟真实 AuditService 的失败语义：注入的底层异常经 UpstreamUnavailable 包装后抛出
    （§10.4：审计写入失败不得静默成功）。
    """

    def __init__(self, *, raise_exc: Exception | None = None) -> None:
        # 不调用 super().__init__，避免依赖 session/clock。
        self.calls: list[dict[str, Any]] = []
        self._raise = raise_exc

    async def append(self, **kwargs: Any) -> str:
        if self._raise is not None:
            # 与真实 AuditService.append 一致：底层异常映射为 UpstreamUnavailable。
            raise UpstreamUnavailable(
                f"audit_log append failed: {self._raise.__class__.__name__}",
                evidence={"actor": kwargs.get("actor"), "action": kwargs.get("action")},
            ) from self._raise
        self.calls.append(kwargs)
        return "01JFAKEAUDITID000000000000"


@pytest.fixture(autouse=True)
def _clear_ctx():
    clear_context()
    yield
    clear_context()


async def test_audit_captures_after_from_dict_return():
    """被装饰函数返回 dict → 作为 after 快照写入 audit_log。"""
    fake = FakeAuditService()

    @audit(action="create", resource="observation_event")
    async def create_event(*, audit: AuditService, payload: dict) -> dict:
        return {"id": "01J1", "baby_id": "01J2", **payload}

    result = await create_event(audit=fake, payload={"amount_ml": 120})
    assert result["id"] == "01J1"
    assert result["amount_ml"] == 120
    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["action"] == "create"
    assert call["resource"] == "observation_event"
    assert call["after"] == {"id": "01J1", "baby_id": "01J2", "amount_ml": 120}
    assert call["before"] is None


async def test_audit_captures_before_via_load_before_hook():
    """load_before 钩子提供 before 快照（操作前旧状态）。"""
    fake = FakeAuditService()

    async def load_old(*, audit: AuditService, rule_id: str, threshold: float) -> dict:
        return {"rule_id": rule_id, "threshold": 38.0}

    @audit(action="update", resource="rule/{rule_id}", load_before=load_old)
    async def update_rule(*, audit: AuditService, rule_id: str, threshold: float) -> AuditResult:
        return AuditResult(after={"rule_id": rule_id, "threshold": threshold}, rule_version="v3")

    await update_rule(audit=fake, rule_id="01JRULE", threshold=38.5)
    call = fake.calls[0]
    assert call["before"] == {"rule_id": "01JRULE", "threshold": 38.0}
    assert call["after"] == {"rule_id": "01JRULE", "threshold": 38.5}
    assert call["rule_version"] == "v3"
    assert call["resource"] == "rule/01JRULE"  # 模板填充


async def test_audit_result_explicit_before_overrides_load_before():
    """AuditResult.before 优先于 load_before 返回值。"""
    fake = FakeAuditService()

    async def load_old(*, audit: AuditService) -> dict:
        return {"from_hook": True}

    @audit(action="update", resource="x", load_before=load_old)
    async def fn(*, audit: AuditService) -> AuditResult:
        return AuditResult(before={"from_result": True}, after={"new": True})

    await fn(audit=fake)
    assert fake.calls[0]["before"] == {"from_result": True}


async def test_audit_actor_from_user_id_context():
    """actor 从 logger contextvars user_id 取（user_id 优先于 device_id）。"""
    bind_context(user_id="01JUSER", device_id="01JDEV")
    fake = FakeAuditService()

    @audit(action="confirm", resource="alert/{alert_id}")
    async def confirm(*, audit: AuditService, alert_id: str) -> dict:
        return {"alert_id": alert_id, "confirmed": True}

    await confirm(audit=fake, alert_id="01JALERT")
    assert fake.calls[0]["actor"] == "01JUSER"


async def test_audit_actor_falls_back_to_device_id_then_system():
    """无 user_id 时用 device_id；都无则 system。"""
    fake = FakeAuditService()

    @audit(action="sync", resource="device")
    async def sync(*, audit: AuditService) -> dict:
        return {"ok": True}

    # 无任何上下文 → system
    await sync(audit=fake)
    assert fake.calls[0]["actor"] == "system"

    # 有 device_id
    bind_context(device_id="01JDEV")
    await sync(audit=fake)
    assert fake.calls[1]["actor"] == "01JDEV"


async def test_audit_llm_call_id_passthrough():
    """AuditResult.llm_call_id 透传到 audit_log（llm_call 动作）。"""
    fake = FakeAuditService()

    @audit(action="llm_call", resource="copilot/analyze")
    async def analyze(*, audit: AuditService) -> AuditResult:
        return AuditResult(after={"summary": "建议观察"}, llm_call_id="01JLLMCALL")

    await analyze(audit=fake)
    assert fake.calls[0]["llm_call_id"] == "01JLLMCALL"
    assert fake.calls[0]["action"] == "llm_call"


async def test_audit_write_failure_raises_upstream_unavailable():
    """审计写入失败 → UpstreamUnavailable，mutating 操作不得静默成功（§10.4）。"""
    fake = FakeAuditService(raise_exc=RuntimeError("DB connection lost"))

    @audit(action="create", resource="event")
    async def create_event(*, audit: AuditService) -> dict:
        return {"id": "01J1"}

    with pytest.raises(UpstreamUnavailable) as exc_info:
        await create_event(audit=fake)
    assert "audit_log append failed" in str(exc_info.value)
    assert exc_info.value.http_status == 503


async def test_audit_missing_audit_param_raises_type_error():
    """缺 audit: AuditService 参数 → TypeError（防误用）。"""
    fake = FakeAuditService()

    @audit(action="create", resource="event")
    async def create_event(audit: AuditService) -> dict:
        return {"id": "01J1"}

    with pytest.raises(TypeError, match="audit: AuditService"):
        await create_event()

    # 也验证位置参数按类型匹配能找到 AuditService。
    await create_event(fake)
    assert len(fake.calls) == 1


async def test_audit_non_dict_non_result_return_still_records():
    """返回 None / 非 dict 时仍记 actor/action/resource（after=None）。"""
    fake = FakeAuditService()

    @audit(action="delete", resource="event/{event_id}")
    async def delete_event(*, audit: AuditService, event_id: str) -> None:
        return None

    await delete_event(audit=fake, event_id="01JEVT")
    call = fake.calls[0]
    assert call["action"] == "delete"
    assert call["resource"] == "event/01JEVT"
    assert call["after"] is None

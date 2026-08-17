# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
"""Privacy Adapter 安全测试（APC-T025）。

覆盖：PII 脱敏（手机/身份证/邮箱）、canary 泄露阻断、媒体出站阻断、
出站策略拒绝、ModelClient 接入 privacy 后 PII 不出站。
asyncio_mode=auto。
"""

from __future__ import annotations

import httpx
import pytest

from server.app.model_gateway.client import SmartProxyModelClient
from server.app.model_gateway.domain import RoutingPlan
from server.app.privacy.adapter import PrivacyAdapter, PrivacyError

JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF"
PNG = b"\x89PNG\r\n\x1a\n"
MP3 = b"ID3\x03\x00"
MP4 = b"\x00\x00\x00\x20ftyp"


# ---- PII 脱敏 ----


def test_redact_phone():
    a = PrivacyAdapter()
    r = a.redact_outbound("我的手机是13800138000")
    assert "13800138000" not in r.redacted
    assert "[PHONE]" in r.redacted
    assert r.blocked["phone"] == 1


def test_redact_id_card():
    a = PrivacyAdapter()
    r = a.redact_outbound("身份证110101199001011234")
    assert "110101199001011234" not in r.redacted
    assert "[IDCARD]" in r.redacted


def test_redact_email():
    a = PrivacyAdapter()
    r = a.redact_outbound("联系我 at user@example.com")
    assert "user@example.com" not in r.redacted
    assert "[EMAIL]" in r.redacted


def test_redact_multiple_pii():
    a = PrivacyAdapter()
    r = a.redact_outbound("电话13800138000，邮箱a@b.com，身份证110101199001011234")
    assert "13800138000" not in r.redacted
    assert "a@b.com" not in r.redacted
    assert "110101199001011234" not in r.redacted
    assert r.blocked["phone"] == 1
    assert r.blocked["email"] == 1
    assert r.blocked["id_card"] == 1


def test_redact_no_pii_unchanged():
    a = PrivacyAdapter()
    r = a.redact_outbound("宝宝今天体温37.2度，状态良好")
    # 无 PII → 原文保留，末尾追加 canary 标记。
    assert r.redacted.startswith("宝宝今天体温37.2度，状态良好")
    assert r.canary in r.redacted
    assert r.blocked == {}


def test_redact_canary_generated():
    a = PrivacyAdapter()
    r = a.redact_outbound("hello")
    assert r.canary.startswith("CNRY_")
    assert len(r.canary) > len("CNRY_")


def test_redact_disabled_passes_through():
    """redact_on_outbound=False → 不脱敏（dev 观察原始数据用），仍注入 canary。"""
    a = PrivacyAdapter(redact_on_outbound=False)
    r = a.redact_outbound("手机13800138000")
    assert "13800138000" in r.redacted  # 未脱敏
    assert r.canary.startswith("CNRY_")


# ---- canary 泄露阻断 ----


def test_canary_leak_blocked():
    a = PrivacyAdapter()
    r = a.redact_outbound("hello")
    # 云端响应回显 canary → 泄露阻断。
    with pytest.raises(PrivacyError, match="canary leak"):
        a.verify_canary(f"回复内容含 {r.canary}", r.canary)


def test_canary_no_leak_passes():
    a = PrivacyAdapter()
    r = a.redact_outbound("hello")
    # 云端响应不含 canary → 通过。
    a.verify_canary("正常回复，无 canary", r.canary)


# ---- 媒体出站阻断 ----


@pytest.mark.parametrize("media", [JPEG, PNG, MP3, MP4])
def test_media_egress_blocked(media: bytes):
    a = PrivacyAdapter()
    with pytest.raises(PrivacyError, match="media egress blocked"):
        a.check_media(media)


def test_media_empty_allowed():
    a = PrivacyAdapter()
    a.check_media(b"")  # 空字节不阻断
    a.check_media(None)


def test_text_payload_allowed():
    """非媒体字节（纯文本）不阻断。"""
    a = PrivacyAdapter()
    a.check_media(b"plain text not media")


# ---- 出站策略 ----


def test_egress_disabled_blocks():
    a = PrivacyAdapter(allow_cloud_egress=False)
    with pytest.raises(PrivacyError, match="cloud egress disabled"):
        a.check_egress_allowed()


def test_egress_allowed_passes():
    a = PrivacyAdapter(allow_cloud_egress=True)
    a.check_egress_allowed()  # 不抛错


# ---- ModelClient 接入 privacy ----


def _client_with_privacy(handler, privacy: PrivacyAdapter) -> SmartProxyModelClient:
    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(base_url="http://127.0.0.1:4000", transport=transport)
    plans = {
        "copilot.triage": RoutingPlan(key="copilot.triage", model="m", max_tokens=100),
        "vision.jaundice": RoutingPlan(
            key="vision.jaundice", model="m", max_tokens=100, is_vision=True
        ),
    }
    return SmartProxyModelClient(
        base_url="http://127.0.0.1:4000", plans=plans, client=http, privacy=privacy
    )


async def test_model_chat_redacts_pii_before_outbound():
    """注入 privacy 后，chat 出站前 PII 脱敏（请求体不含原始手机号）。"""
    captured: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        import json

        captured["body"] = json.loads(req.read())
        return httpx.Response(
            200, json={"model": "m", "content": [{"type": "text", "text": "好的"}]}
        )

    c = _client_with_privacy(handler, PrivacyAdapter())
    r = await c.chat("copilot.triage", [{"role": "user", "content": "手机13800138000"}])
    # 出站请求体已脱敏。
    assert "13800138000" not in str(captured["body"])
    assert "[PHONE]" in str(captured["body"])
    # 响应正常返回。
    assert r.content == "好的"


async def test_model_chat_canary_leak_blocked():
    """云端响应回显 canary → ModelError 阻断。"""
    leak_canary: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        import json

        body = json.loads(req.read())
        # 从请求文本里提取 canary（模拟云端泄露）。
        text = str(body)
        # canary 形如 CNRY_xxxxxxxx；从脱敏文本末尾找。
        leak_canary["canary"] = _extract_canary(text)
        return httpx.Response(
            200,
            json={
                "model": "m",
                "content": [{"type": "text", "text": f"echo {leak_canary['canary']}"}],
            },
        )

    c = _client_with_privacy(handler, PrivacyAdapter())
    with pytest.raises(PrivacyError, match="canary leak"):
        await c.chat("copilot.triage", [{"role": "user", "content": "hi"}])


async def test_model_vision_media_blocked():
    """注入 privacy 后，vision 媒体字节出站阻断。"""
    c = _client_with_privacy(lambda req: httpx.Response(200, json={}), PrivacyAdapter())
    with pytest.raises(PrivacyError, match="media egress blocked"):
        await c.vision("vision.jaundice", JPEG, "评估")


async def test_model_chat_without_privacy_passes_raw():
    """未注入 privacy → 不脱敏（向后兼容 T024 行为）。"""
    captured: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        import json

        captured["body"] = json.loads(req.read())
        return httpx.Response(200, json={"model": "m", "content": [{"type": "text", "text": "ok"}]})

    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(base_url="http://127.0.0.1:4000", transport=transport)
    plans = {"copilot.triage": RoutingPlan(key="copilot.triage", model="m", max_tokens=100)}
    c = SmartProxyModelClient(base_url="http://127.0.0.1:4000", plans=plans, client=http)
    await c.chat("copilot.triage", [{"role": "user", "content": "手机13800138000"}])
    assert "13800138000" in str(captured["body"])  # 未脱敏


def _extract_canary(text: str) -> str:
    import re

    m = re.search(r"CNRY_[0-9a-f]+", text)
    return m.group(0) if m else ""

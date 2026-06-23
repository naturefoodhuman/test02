# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 15:20:00

"""Unit tests for private browser PrivacyGateway pipeline (E8-C4-S1-T1)."""

import asyncio
import json

import pytest

from _infra.network.audit_log.logger import AuditLogger
from _infra.network.exceptions import CanaryTokenDetectedError
from _infra.network.privacy_gateway.canary import CanaryTokenMonitor, DEFAULT_CANARY_TOKEN
from _infra.network.privacy_gateway.gateway import PrivacyGateway
from _infra.network.browser.private_pipeline import PrivateAccessPipeline


class FakePrivateClient:
    def __init__(self, text: str):
        self.text = text
        self.calls = []

    async def get_page_text(self, url=None):
        self.calls.append(url)
        return self.text


def build_gateway() -> PrivacyGateway:
    return PrivacyGateway(
        detectors=[],
        ner_detector=None,
        qwen_classifier=None,
        canary_monitor=CanaryTokenMonitor(tokens=[DEFAULT_CANARY_TOKEN]),
        enable_presidio_default=False,
        enable_ner_default=False,
    )


def test_private_pipeline_redacts_pii_in_full_mode():
    client = FakePrivateClient("Private page phone 13855551234")
    pipeline = PrivateAccessPipeline(client=client, gateway=build_gateway())

    result = asyncio.run(pipeline.process_url("https://github.com/private/repo"))

    assert client.calls == ["https://github.com/private/repo"]
    assert result.redacted.mode == "full"
    assert result.redacted.source_url == "https://github.com/private/repo"
    assert "13855551234" not in result.redacted.text
    assert "PII_CN_PHONE" in result.redacted.text
    assert result.to_output_dict()["schema_valid"] is True


def test_private_pipeline_audit_contains_no_raw_pii(tmp_path):
    audit = AuditLogger(tmp_path / "audit.db")
    client = FakePrivateClient("Private email alice@example.com and phone 13855551234")
    pipeline = PrivateAccessPipeline(client=client, gateway=build_gateway(), audit_logger=audit)

    result = asyncio.run(pipeline.process_url("https://github.com/private/repo"))

    assert result.audit_event_id is not None
    rows = audit.query(event_type="private_access_complete", limit=5)
    assert len(rows) == 1
    details = json.loads(rows[0]["details"])
    assert details["source_url"] == "https://github.com/private/repo"
    assert "CN_PHONE" in details["detection_types"]
    assert "13855551234" not in rows[0]["details"]
    assert "alice@example.com" not in rows[0]["details"]


def test_private_pipeline_canary_blocks():
    client = FakePrivateClient(f"Private leak {DEFAULT_CANARY_TOKEN}_private")
    pipeline = PrivateAccessPipeline(client=client, gateway=build_gateway())

    with pytest.raises(CanaryTokenDetectedError):
        asyncio.run(pipeline.process_url("https://github.com/private/repo"))


def test_private_pipeline_sanitizes_html_before_privacy_gateway():
    html = "<script>evil()</script><main>Phone 13855551234</main>"
    client = FakePrivateClient(html)
    pipeline = PrivateAccessPipeline(client=client, gateway=build_gateway())

    result = asyncio.run(pipeline.process_url("https://github.com/private/repo"))

    assert "evil" not in result.redacted.text
    assert "13855551234" not in result.redacted.text

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 23:55:00


"""APC-T025 tests for project Privacy Gateway adapter."""

from __future__ import annotations

import pytest

from server.app.privacy import PrivacyAdapter, PrivacyBoundaryError, PrivacyRequest


@pytest.mark.asyncio
async def test_privacy_adapter_redacts_email_and_cn_phone() -> None:
    adapter = PrivacyAdapter()

    result = await adapter.redact(
        PrivacyRequest(text="联系 parent@example.com 或 13812345678", source_url="unit")
    )

    assert "parent@example.com" not in result.text
    assert "13812345678" not in result.text
    assert "<<EMAIL_ADDRESS_" in result.text
    assert "<<CN_PHONE_" in result.text
    assert result.schema_valid is True
    assert result.canary_clean is True


@pytest.mark.asyncio
async def test_prepare_cloud_text_returns_redacted_text_only() -> None:
    adapter = PrivacyAdapter()

    text = await adapter.prepare_cloud_text("email: parent@example.com")

    assert text.startswith("email: <<EMAIL_ADDRESS_")


@pytest.mark.asyncio
async def test_privacy_adapter_blocks_canary_leak() -> None:
    adapter = PrivacyAdapter()

    with pytest.raises(Exception, match="Canary token detected"):
        await adapter.prepare_cloud_text("AI_CANARY_DO_NOT_LEAK_2026", source_url="unit")


def test_privacy_adapter_blocks_raw_media_cloud_payload() -> None:
    adapter = PrivacyAdapter()

    with pytest.raises(PrivacyBoundaryError):
        adapter.reject_cloud_media(media_kind="image")

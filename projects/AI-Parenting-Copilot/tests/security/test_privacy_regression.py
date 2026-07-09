# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 10:10:00


"""APC-T058 privacy and canary regression tests."""
from __future__ import annotations

import pytest

from server.app.privacy import PrivacyAdapter, PrivacyBoundaryError, PrivacyRequest


@pytest.mark.asyncio
async def test_cloud_bound_text_is_redacted() -> None:
    result = await PrivacyAdapter().redact(
        PrivacyRequest(text="爸爸邮箱 parent@example.com 电话 13812345678")
    )

    assert "parent@example.com" not in result.text
    assert "13812345678" not in result.text


@pytest.mark.asyncio
async def test_canary_blocks_outbound_text() -> None:
    with pytest.raises(Exception, match="Canary token detected"):
        await PrivacyAdapter().prepare_cloud_text("AI_CANARY_DO_NOT_LEAK_2026")


def test_raw_media_cloud_payload_is_blocked() -> None:
    with pytest.raises(PrivacyBoundaryError):
        PrivacyAdapter().reject_cloud_media(media_kind="video")

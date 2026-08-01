# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 23:20:00


"""APC-T027 Logger Copilot tests."""

from __future__ import annotations

import pytest

from server.app.copilots.base import CopilotRegistry, CopilotRequest
from server.app.copilots.logger_copilot import LoggerCopilot
from server.app.memory import MemorySnapshot


@pytest.mark.asyncio
async def test_logger_copilot_parses_chinese_feeding_candidate() -> None:
    copilot = LoggerCopilot()

    response = await copilot.handle(
        CopilotRequest(text="刚喂了90ml奶", intent="record", baby_id="baby-1"),
        MemorySnapshot(baby_id="baby-1"),
    )

    candidate = response.payload["record_candidate"]
    assert candidate["event_type"] == "feeding"
    assert candidate["normalized_payload"] == {"amount_ml": 90.0}
    assert response.requires_confirmation is True


@pytest.mark.asyncio
async def test_logger_copilot_reuses_common_voice_parser_word_orders() -> None:
    response = await LoggerCopilot().handle(
        CopilotRequest(text="奶 80 毫升", intent="record", baby_id="baby-1"),
        MemorySnapshot(baby_id="baby-1"),
    )

    candidate = response.payload["record_candidate"]
    assert candidate["event_type"] == "feeding"
    assert candidate["normalized_payload"] == {"amount_ml": 80.0}


@pytest.mark.asyncio
async def test_logger_copilot_unknown_input_low_confidence() -> None:
    response = await LoggerCopilot().handle(
        CopilotRequest(text="今天挺好", intent="record"),
        MemorySnapshot(),
    )

    assert response.payload["record_candidate"]["event_type"] == "unknown"
    assert response.payload["record_candidate"]["confidence"] < 0.5


def test_copilot_registry_selects_logger() -> None:
    registry = CopilotRegistry()
    logger = LoggerCopilot()
    registry.register(logger)

    assert registry.select(CopilotRequest(text="尿布", intent="record")) is logger

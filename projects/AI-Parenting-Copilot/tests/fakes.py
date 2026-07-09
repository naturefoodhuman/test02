# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 10:10:00


"""Reusable fake services for integration tests."""

from __future__ import annotations

from server.app.model_gateway.client import FakeModelClient
from server.app.notification.channels.fake import (
    FakeAppFullscreenChannel,
    FakeCameraSpeakerChannel,
    FakeFCMChannel,
    FakeMacSpeakerChannel,
)


def build_fake_notification_channels() -> list[object]:
    return [
        FakeFCMChannel(),
        FakeMacSpeakerChannel(),
        FakeAppFullscreenChannel(),
        FakeCameraSpeakerChannel(),
    ]


__all__ = [
    "FakeAppFullscreenChannel",
    "FakeCameraSpeakerChannel",
    "FakeFCMChannel",
    "FakeMacSpeakerChannel",
    "FakeModelClient",
    "build_fake_notification_channels",
]

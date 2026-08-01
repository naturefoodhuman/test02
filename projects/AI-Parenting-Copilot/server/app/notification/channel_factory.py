# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 00:59:00

"""Notification channel factory for safe local/dev runtime."""

from __future__ import annotations

from server.app.notification.channels.app_fullscreen import AppFullscreenChannel
from server.app.notification.channels.base import NotificationChannel
from server.app.notification.channels.camera_speaker import CameraSpeakerChannel
from server.app.notification.channels.fcm import FCMChannel
from server.app.notification.channels.mac_speaker import MacSpeakerChannel


def build_default_channels(*, include_camera: bool = True) -> list[NotificationChannel]:
    """Build safe-by-default notification channels.

    Real credentials can be injected later; default construction is dry-run for
    external/device side effects while preserving channel fan-out semantics.
    """

    channels: list[NotificationChannel] = [
        FCMChannel(dry_run=True),
        MacSpeakerChannel(dry_run=True),
        AppFullscreenChannel(),
    ]
    if include_camera:
        channels.append(CameraSpeakerChannel(dry_run=True))
    return channels

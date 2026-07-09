# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 05:55:00


"""Fake notification channels for CI/dev."""

from __future__ import annotations

from server.app.notification.alert_repo import AlertRecord
from server.app.notification.channels.base import DeliveryReceipt


class FakeNotificationChannel:
    def __init__(self, name: str, *, fail: bool = False) -> None:
        self.name = name
        self.fail = fail
        self.sent: list[dict[str, object]] = []
        self.cancelled: list[str] = []

    async def send(self, alert: AlertRecord) -> DeliveryReceipt:
        # FCM-like privacy: payload intentionally contains only alert_id/level/type.
        payload: dict[str, object] = {
            "alert_id": alert.id,
            "level": alert.level.value,
            "type": alert.type,
        }
        self.sent.append(payload)
        if self.fail:
            return DeliveryReceipt(
                alert_id=alert.id,
                channel=self.name,
                status="failed",
                receipt={"payload": payload, "error": "fake_failure"},
            )
        return DeliveryReceipt(
            alert_id=alert.id,
            channel=self.name,
            status="sent",
            receipt={"payload": payload},
        )

    async def cancel(self, alert: AlertRecord) -> None:
        self.cancelled.append(alert.id)


class FakeFCMChannel(FakeNotificationChannel):
    def __init__(self, *, fail: bool = False) -> None:
        super().__init__("fcm", fail=fail)


class FakeMacSpeakerChannel(FakeNotificationChannel):
    def __init__(self, *, fail: bool = False) -> None:
        super().__init__("mac_speaker", fail=fail)


class FakeAppFullscreenChannel(FakeNotificationChannel):
    def __init__(self, *, fail: bool = False) -> None:
        super().__init__("app_fullscreen", fail=fail)


class FakeCameraSpeakerChannel(FakeNotificationChannel):
    def __init__(self, *, fail: bool = False) -> None:
        super().__init__("camera_speaker", fail=fail)

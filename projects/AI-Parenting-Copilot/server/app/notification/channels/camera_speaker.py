# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 00:58:00

"""Camera speaker fallback notification channel."""

from __future__ import annotations

from server.app.notification.alert_repo import AlertRecord
from server.app.notification.channels.base import DeliveryReceipt
from server.app.notification.channels.mac_speaker import safe_spoken_alert


class CameraSpeakerChannel:
    name = "camera_speaker"

    def __init__(self, *, dry_run: bool = True, target: str | None = None) -> None:
        self.dry_run = dry_run
        self.target = target
        self.cancelled: list[str] = []

    async def send(self, alert: AlertRecord) -> DeliveryReceipt:
        # Real ISAPI/RTSP speaker integration is device-specific. The adapter keeps
        # the channel contract stable and returns a dry-run receipt until device
        # credentials are configured.
        return DeliveryReceipt(
            alert_id=alert.id,
            channel=self.name,
            target=self.target,
            status="dry_run" if self.dry_run else "failed",
            receipt={"message": safe_spoken_alert(alert), "dry_run": self.dry_run},
        )

    async def cancel(self, alert: AlertRecord) -> None:
        self.cancelled.append(alert.id)

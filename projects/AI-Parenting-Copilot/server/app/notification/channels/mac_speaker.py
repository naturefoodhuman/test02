# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 00:56:00

"""Mac speaker notification channel."""

from __future__ import annotations

import asyncio

from server.app.notification.alert_repo import AlertRecord
from server.app.notification.channels.base import DeliveryReceipt


def safe_spoken_alert(alert: AlertRecord) -> str:
    """Return a short non-medical local alert announcement."""

    level = alert.level.value
    return f"育儿副驾驶提醒：{level} 级告警，请打开手机查看详情并确认。"


class MacSpeakerChannel:
    name = "mac_speaker"

    def __init__(self, *, dry_run: bool = True, command: str = "say") -> None:
        self.dry_run = dry_run
        self.command = command
        self.cancelled: list[str] = []

    async def send(self, alert: AlertRecord) -> DeliveryReceipt:
        message = safe_spoken_alert(alert)
        if self.dry_run:
            return DeliveryReceipt(
                alert_id=alert.id,
                channel=self.name,
                status="dry_run",
                receipt={"message": message, "dry_run": True},
            )
        process = await asyncio.create_subprocess_exec(
            self.command,
            message,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        return_code = await process.wait()
        return DeliveryReceipt(
            alert_id=alert.id,
            channel=self.name,
            status="sent" if return_code == 0 else "failed",
            receipt={"return_code": return_code, "message": message},
        )

    async def cancel(self, alert: AlertRecord) -> None:
        self.cancelled.append(alert.id)

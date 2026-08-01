# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 00:55:00

"""FCM notification channel adapter.

The adapter is safe-by-default: without credentials or with `dry_run=True`, it only
returns a delivery receipt containing the trigger-only payload. It never includes
medical evidence, recommendations, raw input, or other private alert details.
"""

from __future__ import annotations

import httpx

from server.app.notification.alert_repo import AlertRecord
from server.app.notification.channels.base import DeliveryReceipt

FCM_SEND_ENDPOINT = "https://fcm.googleapis.com/fcm/send"


def build_fcm_trigger_payload(alert: AlertRecord) -> dict[str, object]:
    """Return privacy-preserving FCM trigger payload."""

    return {"alert_id": alert.id, "level": alert.level.value, "type": alert.type}


class FCMChannel:
    name = "fcm"

    def __init__(
        self,
        *,
        server_key: str | None = None,
        target_token: str | None = None,
        endpoint: str = FCM_SEND_ENDPOINT,
        dry_run: bool = True,
    ) -> None:
        self.server_key = server_key
        self.target_token = target_token
        self.endpoint = endpoint
        self.dry_run = dry_run

    async def send(self, alert: AlertRecord) -> DeliveryReceipt:
        payload = build_fcm_trigger_payload(alert)
        if self.dry_run or not self.server_key or not self.target_token:
            return DeliveryReceipt(
                alert_id=alert.id,
                channel=self.name,
                target=self.target_token,
                status="dry_run",
                receipt={"payload": payload, "dry_run": True},
            )
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                self.endpoint,
                headers={"authorization": f"key={self.server_key}"},
                json={"to": self.target_token, "data": payload, "priority": "high"},
            )
        return DeliveryReceipt(
            alert_id=alert.id,
            channel=self.name,
            target=self.target_token,
            status="sent" if response.is_success else "failed",
            receipt={"status_code": response.status_code, "payload": payload},
        )

    async def cancel(self, alert: AlertRecord) -> None:
        """FCM one-shot trigger has no cancel API; present for channel protocol symmetry."""

        return None

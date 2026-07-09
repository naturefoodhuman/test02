# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 06:40:00


"""Alert escalation state machine with virtual-clock friendly steps."""

from __future__ import annotations

from dataclasses import dataclass, field

from server.app.notification.alert_repo import AlertRecord, AlertStatus
from server.app.notification.channels.base import DeliveryReceipt
from server.app.notification.orchestrator import NotificationOrchestrator


@dataclass(slots=True)
class EscalationPolicy:
    repeat_seconds: int = 60
    escalate_seconds: int = 90


@dataclass(slots=True)
class EscalationSession:
    alert: AlertRecord
    elapsed_seconds: int = 0
    acknowledged: bool = False
    receipts: list[DeliveryReceipt] = field(default_factory=list)
    stages: list[str] = field(default_factory=list)


class EscalationStateMachine:
    """0s fan-out, 60s Mac repeat, 90s phone/camera escalation, ack cancels."""

    def __init__(
        self,
        orchestrator: NotificationOrchestrator,
        *,
        policy: EscalationPolicy | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.policy = policy or EscalationPolicy()

    async def start(self, alert: AlertRecord) -> EscalationSession:
        session = EscalationSession(alert=alert)
        receipts = await self.orchestrator.dispatch(alert)
        session.receipts.extend(receipts)
        session.stages.append("initial_fanout")
        return session

    async def advance(self, session: EscalationSession, seconds: int) -> EscalationSession:
        if session.acknowledged:
            return session
        session.elapsed_seconds += seconds
        if (
            session.elapsed_seconds >= self.policy.repeat_seconds
            and "mac_repeat" not in session.stages
        ):
            receipt = await self._send_if_available("mac_speaker", session.alert)
            if receipt is not None:
                session.receipts.append(receipt)
            session.stages.append("mac_repeat")
        if (
            session.elapsed_seconds >= self.policy.escalate_seconds
            and "phone_camera_escalate" not in session.stages
        ):
            for channel_name in ["app_fullscreen", "camera_speaker"]:
                receipt = await self._send_if_available(channel_name, session.alert)
                if receipt is not None:
                    session.receipts.append(receipt)
            session.stages.append("phone_camera_escalate")
        return session

    async def ack(
        self,
        session: EscalationSession,
        *,
        ack_by: str,
        device_id: str | None = None,
    ) -> EscalationSession:
        session.acknowledged = True
        session.alert.status = AlertStatus.ACKNOWLEDGED
        session.alert.ack_by = ack_by
        session.alert.ack_device_id = device_id
        session.stages.append("ack_cancelled")
        for channel in self.orchestrator.channels.values():
            cancel = getattr(channel, "cancel", None)
            if cancel is not None:
                await cancel(session.alert)
        return session

    async def _send_if_available(
        self,
        channel_name: str,
        alert: AlertRecord,
    ) -> DeliveryReceipt | None:
        channel = self.orchestrator.channels.get(channel_name)
        if channel is None:
            return None
        receipt = await channel.send(alert)
        await self.orchestrator.delivery_repo.add(receipt)
        return receipt

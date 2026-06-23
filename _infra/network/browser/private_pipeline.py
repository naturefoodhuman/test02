# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 15:20:00

"""Private browser access → Privacy Gateway full-mode pipeline (E8-C4-S1-T1)."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Protocol

from ..audit_log.logger import AuditLogger
from ..audit_log.models import AuditEvent
from ..input_sanitizer.sanitizer import sanitize
from ..privacy_gateway.gateway import PrivacyContext, PrivacyGateway, RedactedContent, build_privacy_gateway
from .chrome_devtools_client import ChromeDevToolsMCPClient


class PrivatePageTextClient(Protocol):
    async def get_page_text(self, url: str | None = None) -> str: ...


@dataclass(frozen=True)
class PrivateAccessResult:
    """Result returned by PrivateAccessPipeline."""

    redacted: RedactedContent
    source_url: str
    audit_event_id: str | None = None

    def to_output_dict(self) -> dict[str, Any]:
        return self.redacted.to_output_dict()


class PrivateAccessPipeline:
    """Run read-only private page text through sanitizer + PrivacyGateway full mode."""

    def __init__(
        self,
        client: PrivatePageTextClient | None = None,
        gateway: PrivacyGateway | None = None,
        audit_logger: AuditLogger | None = None,
    ):
        self.client = client or ChromeDevToolsMCPClient()
        self.gateway = gateway or build_privacy_gateway()
        self.audit_logger = audit_logger

    async def process_url(self, url: str) -> PrivateAccessResult:
        page_text = await self.client.get_page_text(url)
        sanitized = sanitize(page_text, source_url=url, strip_html=True)
        redacted = await self.gateway.process(
            sanitized,
            PrivacyContext(mode="full", source_url=url, require_schema_validation=True),
        )
        audit_id = self._audit(url, redacted)
        return PrivateAccessResult(redacted=redacted, source_url=url, audit_event_id=audit_id)

    def _audit(self, url: str, redacted: RedactedContent) -> str | None:
        if self.audit_logger is None:
            return None
        event = AuditEvent(
            event_type="private_access_complete",
            server_id="chrome-devtools-private",
            tool_name="private_access_pipeline",
            mode="private",
            decision="allow",
            details={
                "source_url": url,
                "mapping_id": redacted.pii_map_id,
                "detection_types": [entity.get("type") for entity in redacted.detections],
                "redacted_length": len(redacted.text),
            },
        )
        return self.audit_logger.record(event)


__all__ = ["PrivateAccessPipeline", "PrivateAccessResult"]

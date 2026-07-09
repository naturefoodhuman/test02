# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-08 23:55:00


"""Project adapter over the factory Privacy Gateway.

Cloud-bound text must pass through this adapter before Model Gateway fallback plans
with `allow_cloud_fallback=true` are allowed to send it onward.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from server.app.common.errors import AppError

FACTORY_ROOT = Path(__file__).resolve().parents[5]


PrivacyMode = Literal["light", "full"]


class PrivacyBoundaryError(AppError):
    """Raised when a payload would cross the project privacy boundary."""

    status_code = 403
    code = "PRIVACY_BOUNDARY_VIOLATION"


def _build_factory_privacy_gateway() -> Any:
    """Load the factory Privacy Gateway without copying its implementation."""

    if str(FACTORY_ROOT) not in sys.path:
        sys.path.insert(0, str(FACTORY_ROOT))
    config_loader = importlib.import_module("_infra.network.config_loader")
    privacy_module = importlib.import_module("_infra.network.privacy_gateway")
    network_config = config_loader.load_network_config(project_root=FACTORY_ROOT)
    return privacy_module.build_privacy_gateway(
        config=network_config,
        require_sqlcipher=False,
        enable_presidio=False,
        enable_ner=False,
        enable_qwen=False,
    )


class PrivacyRequest(BaseModel):
    """Text privacy processing request."""

    text: str
    source_url: str = "ai-parenting-copilot"
    mode: PrivacyMode = "light"


class PrivacyResult(BaseModel):
    """Redacted output safe for downstream model calls."""

    text: str
    mapping_id: str
    entities: list[dict[str, object]] = Field(default_factory=list)
    schema_valid: bool
    canary_clean: bool
    warnings: list[str] = Field(default_factory=list)


class PrivacyAdapter:
    """Adapter that reuses the factory `_infra.network.privacy_gateway` implementation."""

    def __init__(self, gateway: Any | None = None) -> None:
        self.gateway = gateway or _build_factory_privacy_gateway()

    async def redact(self, request: PrivacyRequest) -> PrivacyResult:
        """Redact PII and assert canary cleanliness."""

        redacted = await self.gateway.process_text(
            request.text,
            mode=request.mode,
            source_url=request.source_url,
        )
        output = redacted.to_output_dict()
        return PrivacyResult(
            text=str(output["text"]),
            mapping_id=str(output["mapping_id"]),
            entities=list(output["entities"]),
            schema_valid=bool(output["schema_valid"]),
            canary_clean=bool(output["canary_clean"]),
            warnings=list(redacted.warnings),
        )

    async def prepare_cloud_text(self, text: str, *, source_url: str = "cloud-fallback") -> str:
        """Return redacted text for a cloud-bound prompt segment."""

        return (await self.redact(PrivacyRequest(text=text, source_url=source_url))).text

    def reject_cloud_media(self, *, media_kind: str, reason: str = "raw_media_cloud_block") -> None:
        """Always block raw image/video/audio/media cloud outbound payloads."""

        raise PrivacyBoundaryError(
            "Raw media is not allowed to leave the home LAN",
            evidence={"media_kind": media_kind, "reason": reason},
        )

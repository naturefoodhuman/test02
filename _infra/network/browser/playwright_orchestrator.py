# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 15:35:00

"""High-level Playwright browser orchestrator (E7-C2-S1-T2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from ..exceptions import SessionExpiredError
from .playwright_client import PlaywrightMCPClient
from .profile_manager import BrowserProfile, ProfileManager
from .session_detector import SessionDetectionResult, SessionDetector


@dataclass(frozen=True)
class BrowserExtractionResult:
    """Result of a public browser go-and-extract task."""

    url: str
    text: str
    profile: BrowserProfile
    session: SessionDetectionResult
    raw_snapshot: Mapping[str, Any]
    warnings: list[str] = field(default_factory=list)


class PlaywrightOrchestrator:
    """Small orchestration layer over PlaywrightMCPClient and ProfileManager."""

    def __init__(
        self,
        client: PlaywrightMCPClient | None = None,
        profile_manager: ProfileManager | None = None,
        session_detector: SessionDetector | None = None,
        default_profile: str = "ai_public",
    ):
        self.client = client or PlaywrightMCPClient()
        self.profile_manager = profile_manager or ProfileManager()
        self.session_detector = session_detector or SessionDetector()
        self.default_profile = default_profile

    @staticmethod
    def _snapshot_to_text(snapshot: Mapping[str, Any]) -> str:
        for key in ("text", "content", "aria_snapshot", "snapshot"):
            value = snapshot.get(key)
            if isinstance(value, str):
                return value
        return str(snapshot)

    async def go_and_extract(self, url: str, profile_name: str | None = None) -> BrowserExtractionResult:
        """Navigate to a public URL, take accessibility snapshot, and return text."""
        profile = self.profile_manager.get_profile(profile_name or self.default_profile)
        self.profile_manager.ensure_profile_dir(profile.name)

        await self.client.navigate(url)
        snapshot = await self.client.snapshot()
        text = self._snapshot_to_text(snapshot)
        session = self.session_detector.detect(text)
        if session.expired:
            raise SessionExpiredError(profile.name, url, reason=session.reason, matched_keywords=session.matched_keywords)

        return BrowserExtractionResult(
            url=url,
            text=text,
            profile=profile,
            session=session,
            raw_snapshot=snapshot,
        )

    async def fill_form_field(self, ref: str, text: str) -> dict[str, Any]:
        """Delegate form typing through guarded Playwright client."""
        return await self.client.type_text(ref, text)

    async def close(self) -> dict[str, Any]:
        return await self.client.close()


__all__ = ["BrowserExtractionResult", "PlaywrightOrchestrator"]

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 20:58:00

"""
CanaryTokenMonitor — Privacy Gateway L7 canary leak detector (E5-C8-S1-T1).

Per NETWORK_ARCHITECTURE_FINAL.md §10.9 and TASK_BACKLOG E5-C8-S1-T1.

If a canary token appears in any output/log-like text, the monitor raises
CanaryTokenDetectedError immediately. Audit logging records only masked tokens
and metadata; it never stores the full source text.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Iterable, List, Optional, Pattern

import yaml

from ..audit_log.logger import AuditLogger
from ..audit_log.models import AuditEvent
from ..config_loader import load_network_config
from ..exceptions import CanaryTokenDetectedError

DEFAULT_CANARY_TOKEN = "AI_CANARY_DO_NOT_LEAK_2026"
DEFAULT_CONFIG_PATH = Path("config/canary_tokens.yaml")


@dataclass(frozen=True)
class CanaryHit:
    """One detected canary token occurrence."""

    token: str
    location: str
    start: int
    end: int
    pattern: str

    @property
    def masked_token(self) -> str:
        if len(self.token) <= 12:
            return "***"
        return f"{self.token[:8]}...{self.token[-4:]}"


class CanaryTokenMonitor:
    """Regex-based canary token monitor with optional audit logging."""

    def __init__(
        self,
        tokens: Iterable[str] | None = None,
        patterns: Iterable[str] | None = None,
        audit_logger: AuditLogger | None = None,
        mode: str = "research",
    ):
        self.tokens = list(tokens or [DEFAULT_CANARY_TOKEN])
        self.patterns = list(patterns or [])
        self.audit_logger = audit_logger
        self.mode = mode
        self._compiled: list[Pattern[str]] = [self._compile_token(token) for token in self.tokens]
        self._compiled.extend(re.compile(pattern) for pattern in self.patterns)

    @classmethod
    def from_config(
        cls,
        config_path: str | Path = DEFAULT_CONFIG_PATH,
        audit_logger: AuditLogger | None = None,
        mode: str = "research",
    ) -> "CanaryTokenMonitor":
        """Build monitor from config/canary_tokens.yaml and config/network.yaml."""
        tokens: list[str] = []
        patterns: list[str] = []

        path = Path(config_path)
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            tokens.extend(data.get("canary_tokens", []) or [])
            patterns.extend(data.get("canary_patterns", []) or [])

        try:
            network_cfg = load_network_config()
            tokens.extend(network_cfg.privacy_gateway.canary_tokens)
        except Exception:
            # Config loading must not disable the monitor. Keep defaults below.
            pass

        if not tokens:
            tokens = [DEFAULT_CANARY_TOKEN]

        # Deduplicate while preserving order.
        tokens = list(dict.fromkeys(tokens))
        patterns = list(dict.fromkeys(patterns))
        return cls(tokens=tokens, patterns=patterns, audit_logger=audit_logger, mode=mode)

    @staticmethod
    def _compile_token(token: str) -> Pattern[str]:
        """
        Compile token into a regex.

        A configured token without wildcard also matches underscore-suffixed
        canaries such as ``AI_CANARY_DO_NOT_LEAK_2026_xxxxx``.
        A ``*`` wildcard in config is translated to ``[A-Za-z0-9_-]*``.
        """
        escaped = re.escape(token).replace(r"\*", r"[A-Za-z0-9_-]*")
        if "*" not in token:
            escaped = escaped + r"(?:_[A-Za-z0-9_-]+)?"
        return re.compile(rf"(?<![A-Za-z0-9_]){escaped}(?![A-Za-z0-9_-])")

    def scan(self, text: str, location: str = "unknown") -> List[CanaryHit]:
        """Return all canary hits in text without raising."""
        if not text:
            return []

        hits: list[CanaryHit] = []
        for pattern in self._compiled:
            for match in pattern.finditer(text):
                hits.append(
                    CanaryHit(
                        token=match.group(0),
                        location=location,
                        start=match.start(),
                        end=match.end(),
                        pattern=pattern.pattern,
                    )
                )
        hits.sort(key=lambda hit: hit.start)
        return hits

    def has_canary(self, text: str) -> bool:
        """Fast boolean check."""
        return bool(self.scan(text))

    def assert_clean(self, text: str, location: str = "unknown") -> None:
        """
        Raise CanaryTokenDetectedError on first hit and write audit metadata.

        The raised exception and audit log use masked token values to avoid
        turning the audit trail itself into a canary leak location.
        """
        hits = self.scan(text, location=location)
        if not hits:
            return

        self._audit_hits(hits)
        first = hits[0]
        raise CanaryTokenDetectedError(first.masked_token, location)

    def _audit_hits(self, hits: list[CanaryHit]) -> None:
        if self.audit_logger is None or not hits:
            return

        first = hits[0]
        event = AuditEvent(
            event_type="canary_hit",
            server_id="privacy_gateway",
            tool_name="canary_monitor",
            mode=self.mode,
            decision="blocked",
            details={
                "token": first.masked_token,
                "location": first.location,
                "start": first.start,
                "end": first.end,
                "hit_count": len(hits),
            },
        )
        self.audit_logger.record(event)


__all__ = [
    "CanaryHit",
    "CanaryTokenMonitor",
    "DEFAULT_CANARY_TOKEN",
]

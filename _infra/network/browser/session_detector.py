# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 15:35:00

"""Session expiry / login page detector (E7-C4-S1-T1).

Detects login/CAPTCHA/2FA/verification pages from accessibility snapshot or DOM
text. This component prevents agents from repeatedly trying login/OTP/CAPTCHA
flows and triggering account risk controls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import platform
import re
import subprocess
from typing import Callable, Iterable, Mapping

import yaml

DEFAULT_SESSION_KEYWORDS_PATH = Path("config/session_keywords.yaml")


@dataclass(frozen=True)
class SessionDetectionResult:
    """Result of session/login-state detection."""

    expired: bool
    needs_login: bool = False
    needs_captcha: bool = False
    needs_2fa: bool = False
    needs_verification: bool = False
    matched_keywords: list[str] = field(default_factory=list)
    reason: str = "session_valid"


@dataclass(frozen=True)
class SessionKeywordConfig:
    login_page_patterns: list[str] = field(default_factory=lambda: ["登录", "Sign in", "Login"])
    captcha_patterns: list[str] = field(default_factory=lambda: ["CAPTCHA", "验证码"])
    two_factor_patterns: list[str] = field(default_factory=lambda: ["2FA", "Two-Factor"])
    verification_patterns: list[str] = field(default_factory=lambda: ["Verify", "verification code", "验证"])


class SessionDetector:
    """Detect expired/private sessions from text snapshots."""

    def __init__(
        self,
        config: SessionKeywordConfig | None = None,
        notifier: Callable[[SessionDetectionResult], None] | None = None,
    ):
        self.config = config or self.load_config()
        self.notifier = notifier

    @staticmethod
    def load_config(path: str | Path = DEFAULT_SESSION_KEYWORDS_PATH) -> SessionKeywordConfig:
        cfg_path = Path(path)
        if not cfg_path.exists():
            return SessionKeywordConfig()
        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        return SessionKeywordConfig(
            login_page_patterns=list(data.get("login_page_patterns", []) or []),
            captcha_patterns=list(data.get("captcha_patterns", []) or []),
            two_factor_patterns=list(data.get("two_factor_patterns", []) or []),
            verification_patterns=list(data.get("verification_patterns", []) or []),
        )

    @staticmethod
    def _to_text(snapshot: object) -> str:
        if snapshot is None:
            return ""
        if isinstance(snapshot, str):
            return snapshot
        if isinstance(snapshot, Mapping):
            parts = []
            for key in ("text", "content", "snapshot", "aria_snapshot", "title", "url"):
                value = snapshot.get(key)
                if isinstance(value, str):
                    parts.append(value)
            return "\n".join(parts) if parts else str(snapshot)
        return str(snapshot)

    @staticmethod
    def _find_patterns(text: str, patterns: Iterable[str]) -> list[str]:
        matched = []
        for pattern in patterns:
            if not pattern:
                continue
            if re.search(re.escape(pattern), text, flags=re.IGNORECASE):
                matched.append(pattern)
        return matched

    def detect(self, snapshot: object, *, notify: bool = False) -> SessionDetectionResult:
        text = self._to_text(snapshot)
        login = self._find_patterns(text, self.config.login_page_patterns)
        captcha = self._find_patterns(text, self.config.captcha_patterns)
        two_factor = self._find_patterns(text, self.config.two_factor_patterns)
        verification = self._find_patterns(text, self.config.verification_patterns)

        matched = list(dict.fromkeys(login + captcha + two_factor + verification))
        expired = bool(matched)
        reasons = []
        if login:
            reasons.append("login_required")
        if captcha:
            reasons.append("captcha_required")
        if two_factor:
            reasons.append("two_factor_required")
        if verification:
            reasons.append("verification_required")
        result = SessionDetectionResult(
            expired=expired,
            needs_login=bool(login),
            needs_captcha=bool(captcha),
            needs_2fa=bool(two_factor),
            needs_verification=bool(verification),
            matched_keywords=matched,
            reason=";".join(reasons) if reasons else "session_valid",
        )
        if notify and result.expired:
            self.notify(result)
        return result

    def notify(self, result: SessionDetectionResult) -> None:
        """Notify human. Uses injected notifier or best-effort macOS notification."""
        if self.notifier is not None:
            self.notifier(result)
            return
        if platform.system() != "Darwin":
            return
        message = f"Session attention needed: {result.reason}"
        subprocess.run(
            ["osascript", "-e", f'display notification "{message}" with title "FORGE Network"'],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


__all__ = ["SessionDetectionResult", "SessionDetector", "SessionKeywordConfig"]

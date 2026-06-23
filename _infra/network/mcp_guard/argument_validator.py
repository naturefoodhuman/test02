# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 11:25:00

"""MCP argument safety validator (E2-C4-S1-T4)."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

from _infra.network.privacy_gateway.recognizers.pii_recognizers import detect_common_pii
from _infra.network.privacy_gateway.recognizers.secret_recognizers import detect_secrets

from .models import MCPToolCall

DANGEROUS_ARGUMENT_PATTERNS = (
    r"document\.cookie",
    r"localStorage",
    r"sessionStorage",
    r"eval\s*\(",
    r"Function\s*\(",
)
URL_RE = re.compile(r"https?://[^\s'\"<>]+", re.IGNORECASE)


@dataclass(frozen=True)
class ArgumentValidationResult:
    """Result of argument validation."""

    allowed: bool
    reason: str = "arguments_safe"
    matches: tuple[str, ...] = ()
    arg_length: int = 0


class ArgumentValidator:
    """Validate MCP tool arguments before execution."""

    def __init__(
        self,
        forbidden_patterns: Iterable[str] = DANGEROUS_ARGUMENT_PATTERNS,
        allowed_url_domains: Iterable[str] | None = None,
        max_arg_length: int = 8000,
        detect_pii: bool = True,
        detect_secret: bool = True,
    ):
        self.forbidden_patterns = tuple(re.compile(pattern, re.IGNORECASE) for pattern in forbidden_patterns)
        self.allowed_url_domains = tuple(domain.lower() for domain in (allowed_url_domains or ()))
        self.max_arg_length = max_arg_length
        self.detect_pii = detect_pii
        self.detect_secret = detect_secret

    @staticmethod
    def _serialize_args(args: Mapping[str, Any]) -> str:
        return json.dumps(args, ensure_ascii=False, sort_keys=True, default=str)

    @staticmethod
    def _domain_allowed(url: str, allowed_domains: tuple[str, ...]) -> bool:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if not host:
            return False
        return any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains)

    def validate(self, call: MCPToolCall) -> ArgumentValidationResult:
        arg_text = self._serialize_args(call.args)
        arg_length = len(arg_text)

        if arg_length > self.max_arg_length:
            return ArgumentValidationResult(
                allowed=False,
                reason="arguments_too_long",
                matches=(str(arg_length),),
                arg_length=arg_length,
            )

        matches: list[str] = []
        for pattern in self.forbidden_patterns:
            if pattern.search(arg_text):
                matches.append(pattern.pattern)
        if matches:
            return ArgumentValidationResult(False, "forbidden_argument_pattern", tuple(matches), arg_length)

        if self.allowed_url_domains:
            urls = URL_RE.findall(arg_text)
            disallowed = [url for url in urls if not self._domain_allowed(url, self.allowed_url_domains)]
            if disallowed:
                return ArgumentValidationResult(False, "url_not_allowed", tuple(disallowed), arg_length)

        if self.detect_secret:
            secrets = detect_secrets(arg_text)
            if secrets:
                return ArgumentValidationResult(
                    allowed=False,
                    reason="secret_detected_in_arguments",
                    matches=tuple(entity.type.value for entity in secrets),
                    arg_length=arg_length,
                )

        if self.detect_pii:
            pii = detect_common_pii(arg_text)
            if pii:
                return ArgumentValidationResult(
                    allowed=False,
                    reason="pii_detected_in_arguments",
                    matches=tuple(entity.type.value for entity in pii),
                    arg_length=arg_length,
                )

        return ArgumentValidationResult(True, arg_length=arg_length)


__all__ = ["ArgumentValidationResult", "ArgumentValidator", "DANGEROUS_ARGUMENT_PATTERNS"]

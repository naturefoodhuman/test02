# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 19:41:55

r"""
Secret / token custom recognizers for Privacy Gateway (E5-C3-S1-T4).

Per TASK_BACKLOG E5-C3-S1-T4 + NETWORK_ARCHITECTURE_FINAL.md §10.3.

This module provides two layers:
- ``detect_secrets``: dependency-light deterministic regex scanning returning
  ``PIIEntity`` objects; usable in minimal test environments.
- ``get_secret_recognizers``: optional Microsoft Presidio PatternRecognizers;
  returns an empty list when ``presidio_analyzer`` is not installed.

The deterministic regexes are intentionally conservative and cover only common
high-risk secret formats. They are not a substitute for later PrivacyGateway
L5-L7 placeholder/schema/canary enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, List

from ..models import PIIEntity, PIIType

try:  # Optional dependency: available in full local environment, absent in sandbox.
    from presidio_analyzer import Pattern, PatternRecognizer
except ImportError:  # pragma: no cover - exercised indirectly in minimal env
    Pattern = None  # type: ignore[assignment]
    PatternRecognizer = None  # type: ignore[assignment]


@dataclass(frozen=True)
class SecretPatternSpec:
    """A deterministic secret pattern shared by regex scanner and Presidio."""

    name: str
    entity_type: PIIType
    regex: str
    score: float


SECRET_PATTERN_SPECS: tuple[SecretPatternSpec, ...] = (
    SecretPatternSpec(
        name="jwt",
        entity_type=PIIType.JWT,
        regex=r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b",
        score=0.98,
    ),
    SecretPatternSpec(
        name="github_pat",
        entity_type=PIIType.API_KEY,
        regex=r"\b(?:(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,255}|github_pat_[A-Za-z0-9_]{20,255})\b",
        score=0.98,
    ),
    SecretPatternSpec(
        name="openai_key",
        entity_type=PIIType.API_KEY,
        regex=r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,200}\b",
        score=0.98,
    ),
    SecretPatternSpec(
        name="aws_access_key",
        entity_type=PIIType.API_KEY,
        regex=r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
        score=0.98,
    ),
    SecretPatternSpec(
        name="private_key_header",
        entity_type=PIIType.PRIVATE_KEY,
        regex=r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        score=0.99,
    ),
    SecretPatternSpec(
        name="oauth_bearer",
        entity_type=PIIType.OAUTH_TOKEN,
        regex=r"(?i)\bBearer\s+[A-Za-z0-9_\-.=]{20,}\b",
        score=0.92,
    ),
    SecretPatternSpec(
        name="access_token_assignment",
        entity_type=PIIType.ACCESS_TOKEN,
        regex=r"(?i)\b(?:access[_-]?token|refresh[_-]?token|auth[_-]?token|oauth[_-]?token)\s*[:=]\s*[\"']?[A-Za-z0-9_\-.=]{16,}[\"']?",
        score=0.90,
    ),
    SecretPatternSpec(
        name="api_key_assignment",
        entity_type=PIIType.API_KEY,
        regex=r"(?i)\b(?:api[_-]?key|secret[_-]?key|client[_-]?secret)\s*[:=]\s*[\"']?[A-Za-z0-9_\-.=]{16,}[\"']?",
        score=0.90,
    ),
    SecretPatternSpec(
        name="cookie_header",
        entity_type=PIIType.COOKIE,
        regex=r"(?i)\b(?:cookie|set-cookie)\s*:\s*[^\n]{8,}",
        score=0.88,
    ),
    SecretPatternSpec(
        name="session_id",
        entity_type=PIIType.SESSION_ID,
        regex=r"(?i)\b(?:sessionid|session_id|jsessionid|phpsessid|connect\.sid|csrftoken|xsrf-token)\s*=\s*[^;\s]{8,}",
        score=0.88,
    ),
)


def _ranges_overlap(start: int, end: int, other_start: int, other_end: int) -> bool:
    return start < other_end and other_start < end


def _is_overlapping_existing(start: int, end: int, entities: Iterable[PIIEntity]) -> bool:
    return any(_ranges_overlap(start, end, entity.start, entity.end) for entity in entities)


def detect_secrets(text: str) -> List[PIIEntity]:
    """
    Detect common high-risk secrets using deterministic regexes.

    Returns entities sorted by character offset. Specific high-confidence
    patterns are evaluated before generic assignment patterns; overlapping
    lower-priority matches are skipped to avoid duplicate redaction ranges.
    """
    if not text:
        return []

    entities: list[PIIEntity] = []
    for spec in SECRET_PATTERN_SPECS:
        for match in re.finditer(spec.regex, text):
            start, end = match.span()
            if _is_overlapping_existing(start, end, entities):
                continue
            value = text[start:end]
            entities.append(
                PIIEntity(
                    type=spec.entity_type,
                    value=value,
                    start=start,
                    end=end,
                    score=spec.score,
                    recognizer=f"regex:{spec.name}",
                )
            )

    entities.sort(key=lambda entity: entity.start)
    return entities


def get_secret_recognizers() -> list:
    """
    Return Presidio PatternRecognizer instances for high-risk secrets.

    In minimal environments where ``presidio_analyzer`` is not installed this
    returns an empty list instead of raising ImportError, preserving import
    isolation for the Privacy Gateway base models and ABC.
    """
    if Pattern is None or PatternRecognizer is None:
        return []

    recognizers = []
    for spec in SECRET_PATTERN_SPECS:
        recognizers.append(
            PatternRecognizer(
                supported_entity=spec.entity_type.value,
                patterns=[
                    Pattern(
                        name=spec.name,
                        regex=spec.regex,
                        score=spec.score,
                    )
                ],
                name=f"{spec.name}_recognizer",
                supported_language=None,
            )
        )
    return recognizers


__all__ = [
    "SECRET_PATTERN_SPECS",
    "SecretPatternSpec",
    "detect_secrets",
    "get_secret_recognizers",
]

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 22:05:00

r"""
Deterministic common PII recognizers for Privacy Gateway (E11-C4 hardening).

Purpose:
- Provide dependency-light PII detection for bypass/security tests.
- Cover common PII forms even when optional Presidio/spaCy dependencies are not
  installed in minimal environments.

Covered patterns:
- Chinese mobile phone numbers, including separators / table-split digits
- Email addresses
- Chinese ID card numbers
- Luhn-valid bank cards
- Base64-encoded PII payloads

These recognizers complement Presidio; they do not replace it.
"""

from __future__ import annotations

import base64
import re
from typing import Iterable, List

from ..models import PIIEntity, PIIType

_SEPARATOR = r"[\s\-_.|:：/\\()\[\]{}<>]*"
CN_PHONE_PATTERN = re.compile(rf"(?<!\d)1{_SEPARATOR}[3-9](?:{_SEPARATOR}\d){{9}}(?!\d)")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
CN_ID_PATTERN = re.compile(rf"(?<!\d)\d(?:{_SEPARATOR}\d){{16}}{_SEPARATOR}[\dXx](?!\d)")
BANK_CARD_PATTERN = re.compile(rf"(?<!\d)\d(?:{_SEPARATOR}\d){{12,18}}(?!\d)")
BASE64_TOKEN_PATTERN = re.compile(r"\b[A-Za-z0-9+/]{8,}={0,2}\b")


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def _luhn_valid(number: str) -> bool:
    digits = [int(ch) for ch in number if ch.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, digit in enumerate(digits):
        if i % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def _overlaps(start: int, end: int, entities: Iterable[PIIEntity]) -> bool:
    return any(start < entity.end and entity.start < end for entity in entities)


def _entity(entity_type: PIIType, value: str, start: int, recognizer: str, score: float = 0.95) -> PIIEntity:
    return PIIEntity(
        type=entity_type,
        value=value,
        start=start,
        end=start + len(value),
        score=score,
        recognizer=recognizer,
    )


def _looks_base64(token: str) -> bool:
    if len(token) < 8:
        return False
    # add padding for unpadded tokens
    padded = token + "=" * (-len(token) % 4)
    try:
        decoded = base64.b64decode(padded, validate=True)
        decoded_text = decoded.decode("utf-8", errors="strict")
    except Exception:
        return False
    if not decoded_text or not decoded_text.isprintable():
        return False
    return True


def _decode_base64(token: str) -> str | None:
    padded = token + "=" * (-len(token) % 4)
    try:
        return base64.b64decode(padded, validate=True).decode("utf-8", errors="strict")
    except Exception:
        return None


def detect_common_pii(text: str, *, decode_base64: bool = True) -> List[PIIEntity]:
    """Detect common PII patterns using deterministic regexes."""
    if not text:
        return []

    entities: list[PIIEntity] = []

    for match in CN_PHONE_PATTERN.finditer(text):
        value = match.group(0)
        digits = _digits(value)
        if re.fullmatch(r"1[3-9]\d{9}", digits):
            entities.append(_entity(PIIType.CN_PHONE, value, match.start(), "regex:cn_phone", 0.97))

    for match in EMAIL_PATTERN.finditer(text):
        if not _overlaps(match.start(), match.end(), entities):
            entities.append(_entity(PIIType.EMAIL_ADDRESS, match.group(0), match.start(), "regex:email", 0.95))

    for match in CN_ID_PATTERN.finditer(text):
        value = match.group(0)
        compact = re.sub(r"[^0-9Xx]", "", value)
        if re.fullmatch(r"\d{17}[\dXx]", compact) and not _overlaps(match.start(), match.end(), entities):
            entities.append(_entity(PIIType.CN_ID_CARD, value, match.start(), "regex:cn_id_card", 0.90))

    for match in BANK_CARD_PATTERN.finditer(text):
        value = match.group(0)
        compact = _digits(value)
        if _luhn_valid(compact) and not _overlaps(match.start(), match.end(), entities):
            entities.append(_entity(PIIType.BANK_CARD, value, match.start(), "regex:bank_card_luhn", 0.86))

    if decode_base64:
        for match in BASE64_TOKEN_PATTERN.finditer(text):
            token = match.group(0)
            if _overlaps(match.start(), match.end(), entities) or not _looks_base64(token):
                continue
            decoded = _decode_base64(token)
            if not decoded:
                continue
            decoded_entities = detect_common_pii(decoded, decode_base64=False)
            if decoded_entities:
                first = decoded_entities[0]
                entities.append(
                    _entity(
                        first.type,
                        token,
                        match.start(),
                        f"regex:base64:{first.type.value.lower()}",
                        0.88,
                    )
                )

    entities.sort(key=lambda entity: entity.start)
    return entities


__all__ = ["detect_common_pii"]

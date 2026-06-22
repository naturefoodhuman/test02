r"""
Chinese PII custom recognizers for Presidio (E5-C3-S1-T3)

Per TASK_BACKLOG E5-C3-S1-T3 + NETWORK_ENGINEERING_DESIGN

Language-agnostic regex-based recognizers for Chinese PII.
"""

from __future__ import annotations

import re
from typing import List

from presidio_analyzer import Pattern, PatternRecognizer

# ===================== CN_PHONE =====================
_CN_PHONE_REGEX = r"1[3-9]\d{9}"

CN_PHONE_PATTERN = Pattern(
    name="cn_phone",
    regex=_CN_PHONE_REGEX,
    score=0.95,
)

CN_PHONE_RECOGNIZER = PatternRecognizer(
    supported_entity="CN_PHONE",
    patterns=[CN_PHONE_PATTERN],
    name="cn_phone_recognizer",
    # Make it language-agnostic so it works with 'en' analyzer too
    supported_language=None,
)

# ===================== CN_ID_CARD =====================
_CN_ID_REGEX = r"\d{17}[\dXx]"

CN_ID_PATTERN = Pattern(
    name="cn_id_card",
    regex=_CN_ID_REGEX,
    score=0.85,
)

CN_ID_RECOGNIZER = PatternRecognizer(
    supported_entity="CN_ID_CARD",
    patterns=[CN_ID_PATTERN],
    name="cn_id_card_recognizer",
    supported_language=None,
)

# ===================== BANK_CARD (Luhn) =====================
_BANK_REGEX = r"\b(?:\d[ -]?){13,19}\d\b"

def _luhn_valid(card: str) -> bool:
    digits = [int(d) for d in card if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0

def _validate_bank_card(text: str, start: int, end: int) -> bool:
    raw = text[start:end]
    card = re.sub(r"[ -]", "", raw)
    return _luhn_valid(card)

BANK_PATTERN = Pattern(
    name="bank_card",
    regex=_BANK_REGEX,
    score=0.7,
)

BANK_RECOGNIZER = PatternRecognizer(
    supported_entity="BANK_CARD",
    patterns=[BANK_PATTERN],
    name="bank_card_recognizer",
    supported_language=None,
)

# ===================== CN_ADDRESS (keyword) =====================
_CN_ADDR_KEYWORDS = [
    "省", "市", "区", "县", "镇", "乡", "街道", "路", "号", "巷", "弄",
    "北京", "上海", "广州", "深圳", "天津", "重庆",
    "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江",
    "江苏", "浙江", "安徽", "福建", "江西", "山东",
    "河南", "湖北", "湖南", "广东", "广西", "海南",
    "四川", "贵州", "云南", "西藏", "陕西", "甘肃",
    "青海", "宁夏", "新疆", "香港", "澳门", "台湾"
]

_CN_ADDR_REGEX = r".{2,40}(?:" + "|".join(re.escape(k) for k in _CN_ADDR_KEYWORDS) + r").{0,30}"

CN_ADDRESS_PATTERN = Pattern(
    name="cn_address",
    regex=_CN_ADDR_REGEX,
    score=0.55,
)

CN_ADDRESS_RECOGNIZER = PatternRecognizer(
    supported_entity="CN_ADDRESS",
    patterns=[CN_ADDRESS_PATTERN],
    name="cn_address_recognizer",
    supported_language=None,
)

# ===================== Public API =====================
def get_cn_recognizers() -> List[PatternRecognizer]:
    """Return all Chinese custom recognizers (language-agnostic)."""
    return [
        CN_PHONE_RECOGNIZER,
        CN_ID_RECOGNIZER,
        BANK_RECOGNIZER,
        CN_ADDRESS_RECOGNIZER,
    ]

__all__ = [
    "get_cn_recognizers",
    "CN_PHONE_RECOGNIZER",
    "CN_ID_RECOGNIZER",
    "BANK_RECOGNIZER",
    "CN_ADDRESS_RECOGNIZER",
]

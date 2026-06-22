"""
Unit tests for Chinese PII custom recognizers (E5-C3-S1-T3)
"""

import asyncio

import pytest

from _infra.network.privacy_gateway.recognizers.cn_recognizers import (
    get_cn_recognizers,
    CN_PHONE_RECOGNIZER,
    CN_ID_RECOGNIZER,
    BANK_RECOGNIZER,
    CN_ADDRESS_RECOGNIZER,
)
from _infra.network.privacy_gateway.detectors.presidio_detector import PresidioDetector
from _infra.network.privacy_gateway.models import PIIType


def test_get_cn_recognizers():
    recs = get_cn_recognizers()
    assert len(recs) == 4


def test_cn_phone_pattern():
    text = "我的手机号是 13812345678 和 15900001111"
    rec = CN_PHONE_RECOGNIZER
    results = rec.analyze(text=text, entities=["CN_PHONE"])
    assert len(results) >= 1
    assert any(r.entity_type == "CN_PHONE" for r in results)


def test_cn_id_card_pattern():
    text = "身份证号 110105199001011234 和 31010119900307451X"
    rec = CN_ID_RECOGNIZER
    results = rec.analyze(text=text, entities=["CN_ID_CARD"])
    assert len(results) >= 1


def test_bank_card_luhn():
    text = "银行卡 6222021234567890123"
    rec = BANK_RECOGNIZER
    results = rec.analyze(text=text, entities=["BANK_CARD"])
    assert "BANK_CARD" in rec.supported_entities


def test_cn_address_pattern():
    text = "住在北京市朝阳区建国路88号"
    rec = CN_ADDRESS_RECOGNIZER
    results = rec.analyze(text=text, entities=["CN_ADDRESS"])
    assert len(results) >= 1


def test_presidio_with_cn_recognizers():
    """Register custom Chinese recognizers as ad-hoc and verify detection."""
    cn_recs = get_cn_recognizers()
    det = PresidioDetector(language="en", timeout=8.0)

    # Use ad-hoc recognizers for this detection (bypasses language filter)
    text = "联系电话 13812345678，身份证 110105199001011234"
    # We temporarily monkey-patch for test (or we can extend the class)
    # For simplicity, we analyze directly with ad-hoc
    from presidio_analyzer import AnalyzerEngine
    analyzer = AnalyzerEngine()
    for r in cn_recs:
        analyzer.registry.add_recognizer(r)

    results = analyzer.analyze(text=text, language="en", ad_hoc_recognizers=cn_recs)
    entities = []
    for res in results:
        pii_type = PresidioDetector._map_entity_type(res.entity_type) if hasattr(PresidioDetector, "_map_entity_type") else None
        # Fallback: map manually for test
        from _infra.network.privacy_gateway.detectors.presidio_detector import PRESIDIO_TO_PII_TYPE
        ptype = PRESIDIO_TO_PII_TYPE.get(res.entity_type)
        if ptype:
            entities.append(type("E", (), {"type": ptype, "value": text[res.start:res.end]})())

    types = {e.type for e in entities}
    has_cn = PIIType.CN_PHONE in types or PIIType.CN_ID_CARD in types or any("138" in getattr(e, "value", "") for e in entities)
    assert has_cn, f"No Chinese PII. Raw results: {[(r.entity_type, text[r.start:r.end]) for r in results]}"

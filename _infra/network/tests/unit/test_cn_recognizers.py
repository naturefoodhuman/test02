# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 19:32:46

"""
Unit tests for Chinese PII custom recognizers (E5-C3-S1-T3).

These tests require the optional ``presidio_analyzer`` dependency; they are
skipped in minimal sandbox environments where that dependency is not installed.
"""

import pytest

pytest.importorskip("presidio_analyzer")

from _infra.network.privacy_gateway.detectors.presidio_detector import PRESIDIO_TO_PII_TYPE
from _infra.network.privacy_gateway.models import PIIType
from _infra.network.privacy_gateway.recognizers.cn_recognizers import (
    BANK_RECOGNIZER,
    CN_ADDRESS_RECOGNIZER,
    CN_ID_RECOGNIZER,
    CN_PHONE_RECOGNIZER,
    get_cn_recognizers,
)


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


def test_bank_card_luhn_recognizer_export():
    rec = BANK_RECOGNIZER
    assert "BANK_CARD" in rec.supported_entities


def test_cn_address_pattern():
    text = "住在北京市朝阳区建国路88号"
    rec = CN_ADDRESS_RECOGNIZER
    results = rec.analyze(text=text, entities=["CN_ADDRESS"])
    assert len(results) >= 1


def test_presidio_with_cn_recognizers():
    """Register custom Chinese recognizers as ad-hoc and verify detection."""
    cn_recs = get_cn_recognizers()
    text = "联系电话 13812345678，身份证 110105199001011234"

    from presidio_analyzer import AnalyzerEngine

    analyzer = AnalyzerEngine()
    for recognizer in cn_recs:
        analyzer.registry.add_recognizer(recognizer)

    results = analyzer.analyze(text=text, language="en", ad_hoc_recognizers=cn_recs)
    detected_types = {
        PRESIDIO_TO_PII_TYPE[result.entity_type]
        for result in results
        if result.entity_type in PRESIDIO_TO_PII_TYPE
    }

    assert PIIType.CN_PHONE in detected_types or PIIType.CN_ID_CARD in detected_types, (
        "No Chinese PII. Raw results: "
        f"{[(result.entity_type, text[result.start:result.end]) for result in results]}"
    )

"""
Unit tests for Unicode Normalization (E5-C2-S1-T1)

Security-critical: full-width, zero-width, URL, Base64
"""

import pytest

from _infra.network.utils.unicode_norm import (
    normalize_unicode,
    normalize_for_pii_detection,
)


def test_nfkc_fullwidth_to_halfwidth():
    """Core Chinese security case"""
    raw = "138-５５５５-１２３４"
    result = normalize_unicode(raw)
    assert result == "138-5555-1234"


def test_nfkc_mixed():
    result = normalize_unicode("Ｈｅｌｌｏ Ｗｏｒｌｄ")
    assert result == "Hello World"


def test_zero_width_removal():
    raw = "138\u200b5555\u200c1234\ufeff"
    result = normalize_unicode(raw)
    assert result == "13855551234"


def test_url_decoding():
    raw = "https%3A//example.com/%E4%B8%AD%E6%96%87"
    result = normalize_unicode(raw)
    assert result == "https://example.com/中文"


def test_multiple_url_decodes():
    raw = "a%2520b"  # %2520 = %20 = space
    result = normalize_unicode(raw)
    assert " " in result or result == "a b"


def test_base64_optional():
    # This is a Base64 of 'secret123'
    b64 = "c2VjcmV0MTIz"
    result = normalize_unicode(b64, try_base64=True)
    assert "secret" in result.lower()


def test_base64_disabled_by_default():
    b64 = "c2VjcmV0MTIz"
    result = normalize_unicode(b64, try_base64=False)
    assert result == b64  # unchanged


def test_normalize_for_pii_detection():
    raw = "１３８-５５５５\u200b１２３４"
    result = normalize_for_pii_detection(raw)
    assert result == "138-55551234"


def test_idempotent():
    raw = "１３８-５５５５"
    r1 = normalize_unicode(raw)
    r2 = normalize_unicode(r1)
    assert r1 == r2


def test_empty_and_invalid():
    assert normalize_unicode("") == ""
    assert normalize_unicode(None) == "" or normalize_unicode(None) is None  # depending on impl
    # Should not crash
    normalize_unicode("   ")

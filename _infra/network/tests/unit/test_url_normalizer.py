"""
Unit tests for URL Normalizer (E3-C3-S1-T1)

Covers:
- Tracking param removal
- HTTPS enforcement
- Trailing slash normalization
- Hostname lowercasing
- Dedup equivalence
"""

import pytest

from _infra.network.search.url_normalizer import normalize_url, is_same_url


def test_basic_normalization():
    url = "http://Example.COM:443/path/?utm_source=twitter&fbclid=abc123"
    result = normalize_url(url)
    assert result == "https://example.com/path"
    assert result.startswith("https://")


def test_remove_multiple_tracking():
    url = "https://example.com/article?id=1&utm_campaign=foo&gclid=bar&ref=link"
    result = normalize_url(url)
    assert "utm_campaign" not in result
    assert "gclid" not in result
    assert "ref" not in result
    assert "id=1" in result


def test_preserve_legit_params():
    url = "https://example.com/search?q=python&lang=en"
    result = normalize_url(url)
    assert "q=python" in result
    assert "lang=en" in result


def test_trailing_slash_root():
    assert normalize_url("https://example.com/") == "https://example.com/"
    assert normalize_url("https://example.com") == "https://example.com/"


def test_trailing_slash_nonroot():
    assert normalize_url("https://example.com/foo/") == "https://example.com/foo"
    assert normalize_url("https://example.com/foo/bar/") == "https://example.com/foo/bar"


def test_hostname_lowercase():
    url = "https://WWW.GitHub.COM/python/cpython"
    assert normalize_url(url) == "https://www.github.com/python/cpython"


def test_is_same_url():
    u1 = "http://Example.com/path?utm_source=x"
    u2 = "https://example.com/path"
    assert is_same_url(u1, u2) is True

    u3 = "https://example.com/other"
    assert is_same_url(u1, u3) is False


def test_empty_and_invalid():
    with pytest.raises(ValueError):
        normalize_url("")

    # Should not crash on bad input
    result = normalize_url("not a url")
    assert "not a url" in result or result == "not a url"


def test_fragment_removal():
    url = "https://example.com/page#section?utm=1"
    result = normalize_url(url)
    assert "#" not in result
    assert "utm" not in result

"""Unit tests for optional curl_cffi extractor fallback."""

from _infra.network.extract.curl_cffi_fallback import CURL_CFFI_AVAILABLE, CurlCffiProvider


def test_curl_cffi_provider_only_handles_guarded_domains_when_available():
    provider = CurlCffiProvider()
    if CURL_CFFI_AVAILABLE:
        assert provider.can_handle("https://foo.cloudflare.com/path") is True
        assert provider.can_handle("https://example.com/path") is False
    else:
        assert provider.can_handle("https://foo.cloudflare.com/path") is False

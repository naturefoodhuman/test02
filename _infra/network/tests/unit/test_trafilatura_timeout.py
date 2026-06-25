"""Unit tests for bounded trafilatura fallback."""

import asyncio

import httpx
import pytest

import _infra.network.extract.trafilatura_fallback as tf
from _infra.network.extract.trafilatura_fallback import TrafilaturaProvider


def test_trafilatura_provider_timeout(monkeypatch):
    if tf.trafilatura is None:
        pytest.skip("trafilatura not installed")

    async def raise_timeout(url):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(TrafilaturaProvider, "_download", raise_timeout)

    async def run_test():
        provider = TrafilaturaProvider(timeout_seconds=0.01)
        result = await provider.extract("https://example.com")
        assert result.content == ""
        assert "timeout" in result.error

    asyncio.run(run_test())

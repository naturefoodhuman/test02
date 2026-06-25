"""Unit tests for bounded trafilatura fallback."""

import asyncio
import time

import pytest

import _infra.network.extract.trafilatura_fallback as tf
from _infra.network.extract.trafilatura_fallback import TrafilaturaProvider


def test_trafilatura_provider_timeout(monkeypatch):
    if tf.trafilatura is None:
        pytest.skip("trafilatura not installed")

    def slow_fetch(url):
        time.sleep(0.2)
        return "<html><body>slow</body></html>"

    monkeypatch.setattr(tf.trafilatura, "fetch_url", slow_fetch)

    async def run_test():
        provider = TrafilaturaProvider(timeout_seconds=0.01)
        result = await provider.extract("https://example.com")
        assert result.content == ""
        assert "timeout" in result.error

    asyncio.run(run_test())

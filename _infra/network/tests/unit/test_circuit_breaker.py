"""Unit tests for engine circuit breaker."""

import time

from _infra.network.search.circuit_breaker import EngineCircuitBreaker, EngineState


def test_circuit_breaker_opens_after_threshold():
    breaker = EngineCircuitBreaker(failure_threshold=2, initial_cooldown_s=10)
    assert breaker.is_available("duckduckgo") is True
    breaker.record_failure("duckduckgo", "captcha")
    assert breaker.get("duckduckgo").state == EngineState.CLOSED
    breaker.record_failure("duckduckgo", "captcha")
    assert breaker.get("duckduckgo").state == EngineState.OPEN
    assert breaker.is_available("duckduckgo") is False


def test_circuit_breaker_half_open_then_success():
    breaker = EngineCircuitBreaker(failure_threshold=1, initial_cooldown_s=0.01)
    breaker.record_failure("bing", "timeout")
    assert breaker.get("bing").state == EngineState.OPEN
    time.sleep(0.02)
    assert breaker.is_available("bing") is True
    assert breaker.get("bing").state == EngineState.HALF_OPEN
    breaker.record_success("bing")
    assert breaker.get("bing").state == EngineState.CLOSED


def test_filter_engines_skips_open():
    breaker = EngineCircuitBreaker(failure_threshold=1, initial_cooldown_s=10)
    breaker.record_failure("google", "captcha")
    assert breaker.filter_engines(["google", "wikipedia"]) == ["wikipedia"]

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-25 00:00:00

"""
Engine Circuit Breaker - per-engine health tracking for SearXNG engines.

This is an application-layer resilience guard for the Network Increment search
module. It does not change the architecture boundary: SearXNG remains the
primary local search service, while this module avoids repeatedly calling
engines that are currently CAPTCHA/rate-limit blocked.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import Dict

from _infra.network.utils.logger import get_logger

logger = get_logger("network.search.breaker")


class EngineState(str, Enum):
    """Circuit breaker state for a single upstream search engine."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class EngineHealth:
    """Mutable health counters for one SearXNG engine."""

    name: str
    state: EngineState = EngineState.CLOSED
    consecutive_failures: int = 0
    total_calls: int = 0
    total_failures: int = 0
    last_failure_ts: float = 0.0
    open_until_ts: float = 0.0
    last_failure_reason: str = ""

    @property
    def failure_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_failures / self.total_calls


class EngineCircuitBreaker:
    """
    Thread-safe engine-level circuit breaker.

    Policy:
    - CLOSED: normal operation.
    - OPEN: engine skipped until cooldown expires.
    - HALF_OPEN: one probe allowed after cooldown.
    - Consecutive failures or a failed HALF_OPEN probe opens the circuit.
    - Cooldown uses bounded exponential backoff.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        initial_cooldown_s: float = 60.0,
        max_cooldown_s: float = 1800.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.initial_cooldown_s = initial_cooldown_s
        self.max_cooldown_s = max_cooldown_s
        self._health: Dict[str, EngineHealth] = {}
        self._cooldown_multiplier: Dict[str, int] = {}
        self._lock = Lock()

    def _get(self, engine: str) -> EngineHealth:
        normalized = engine.strip().lower()
        if normalized not in self._health:
            self._health[normalized] = EngineHealth(name=normalized)
            self._cooldown_multiplier[normalized] = 0
        return self._health[normalized]

    def get(self, engine: str) -> EngineHealth:
        """Return the current health object for an engine."""
        with self._lock:
            return self._get(engine)

    def is_available(self, engine: str) -> bool:
        """Return whether an engine may be called now."""
        with self._lock:
            h = self._get(engine)
            now = time.time()
            if h.state == EngineState.OPEN:
                if now >= h.open_until_ts:
                    h.state = EngineState.HALF_OPEN
                    logger.info("engine circuit half-open", engine=engine)
                    return True
                return False
            return True

    def record_success(self, engine: str) -> None:
        """Record a successful upstream engine response."""
        with self._lock:
            h = self._get(engine)
            h.total_calls += 1
            h.consecutive_failures = 0
            if h.state in (EngineState.HALF_OPEN, EngineState.OPEN):
                logger.info("engine circuit recovered", engine=engine, previous_state=h.state.value)
                self._cooldown_multiplier[h.name] = 0
            h.state = EngineState.CLOSED
            h.open_until_ts = 0.0

    def record_failure(self, engine: str, reason: str = "") -> None:
        """Record a failed upstream engine response."""
        with self._lock:
            h = self._get(engine)
            h.total_calls += 1
            h.total_failures += 1
            h.consecutive_failures += 1
            h.last_failure_ts = time.time()
            h.last_failure_reason = reason

            if h.consecutive_failures >= self.failure_threshold or h.state == EngineState.HALF_OPEN:
                mult = self._cooldown_multiplier[h.name]
                cooldown = min(self.initial_cooldown_s * (2**mult), self.max_cooldown_s)
                h.state = EngineState.OPEN
                h.open_until_ts = time.time() + cooldown
                self._cooldown_multiplier[h.name] = min(mult + 1, 5)
                logger.warning(
                    "engine circuit opened",
                    engine=engine,
                    cooldown_s=round(cooldown, 1),
                    consecutive_failures=h.consecutive_failures,
                    reason=reason,
                )

    def filter_engines(self, engines: list[str]) -> list[str]:
        """Remove currently OPEN engines from a candidate list."""
        return [engine for engine in engines if self.is_available(engine)]

    def reset(self) -> None:
        """Reset all breaker state. Intended for tests and manual diagnostics."""
        with self._lock:
            self._health.clear()
            self._cooldown_multiplier.clear()

    def snapshot(self) -> Dict[str, dict]:
        """Return serializable health state for diagnostics / logs."""
        with self._lock:
            now = time.time()
            return {
                name: {
                    "state": h.state.value,
                    "failure_rate": round(h.failure_rate, 3),
                    "consecutive_failures": h.consecutive_failures,
                    "total_calls": h.total_calls,
                    "total_failures": h.total_failures,
                    "last_failure_reason": h.last_failure_reason,
                    "cooldown_remaining_s": round(max(0.0, h.open_until_ts - now), 1),
                }
                for name, h in self._health.items()
            }


_global_breaker = EngineCircuitBreaker()


def get_global_breaker() -> EngineCircuitBreaker:
    """Return the process-local engine circuit breaker singleton."""
    return _global_breaker

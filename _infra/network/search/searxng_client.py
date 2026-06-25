# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-25 00:00:00

"""SearXNGProvider v24 - circuit-broken tiered routing for anti-risk-control."""

from __future__ import annotations

from typing import Any, List, Optional

import httpx

from _infra.network.config_loader import load_network_config
from _infra.network.exceptions import SearchEngineUnavailable, SearchRateLimited, SearchResultEmpty
from _infra.network.utils.logger import get_logger

from .base import SearchProvider
from .circuit_breaker import get_global_breaker
from .models import SearchResult

logger = get_logger("network.search.searxng")

# Tuned from 2026-06-25 user real-machine diagnostics:
# healthy: github / arxiv / stackoverflow / hackernews / lobste.rs
# avoid for default routing on current proxy: bing / qwant / mojeek / reddit / DDG / Google / Brave / Startpage.
# Wikipedia is kept as a knowledge/health engine but not treated as broad web search.
ENGINE_TIERS: dict[str, list[str]] = {
    "tier1_stable": ["github", "arxiv", "hackernews", "lobste.rs", "stackoverflow"],
    "tier2_knowledge": ["wikipedia", "wikidata"],
    "tier3_academic": ["crossref", "pubmed", "semantic scholar"],
    "tier4_general_api_trigger": [],
    "tier5_risky": [],
}

FALLBACK_ENGINE_POOL = ["github", "arxiv", "stackoverflow", "hackernews", "lobste.rs", "wikipedia"]


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))


def classify_engine_error(reason: str) -> str:
    """Classify SearXNG unresponsive engine reasons for breaker logs."""
    r = reason.lower()
    if any(k in r for k in ("captcha", "challenge", "bot", "turnstile")):
        return "captcha"
    if any(k in r for k in ("too many", "rate", "suspended", "limit", "429")):
        return "rate_limit"
    if any(k in r for k in ("timeout", "connect", "readtimeout")):
        return "timeout"
    if any(k in r for k in ("forbidden", "denied", "403", "blocked")):
        return "forbidden"
    return "unknown"


class SearXNGProvider(SearchProvider):
    """SearXNG JSON API provider with per-engine circuit breaker."""

    def __init__(self, config: Any = None, client: httpx.AsyncClient | None = None):
        if config is None:
            cfg = load_network_config().search.searxng
        else:
            cfg = config
        self.base_url = getattr(cfg, "base_url", "http://127.0.0.1:8090").rstrip("/")
        self.timeout = getattr(cfg, "timeout_seconds", 30)
        self.engines_enabled = list(getattr(cfg, "engines_enabled", []) or [])
        self.engines_disabled = list(getattr(cfg, "engines_disabled", ["google", "brave", "startpage"]) or [])
        self._client = client
        self.breaker = get_global_breaker()

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"},
                proxy=None,
                trust_env=False,
            )
        return self._client

    async def _fetch_results(
        self,
        query: str,
        limit: int,
        engines_str: Optional[str] = None,
    ) -> tuple[List[SearchResult], List[Any]]:
        engines = [e.strip() for e in engines_str.split(",") if e.strip()] if engines_str else None
        return await self._fetch(query, limit, engines)

    async def _fetch(
        self,
        query: str,
        limit: int,
        engines: Optional[List[str]] = None,
    ) -> tuple[List[SearchResult], List[Any]]:
        params: dict[str, Any] = {"q": query, "format": "json", "limit": limit}
        if engines:
            params["engines"] = ",".join(engines)
        resp = await self.client.get("/search", params=params)
        resp.raise_for_status()
        data = resp.json()
        unresponsive = data.get("unresponsive_engines", [])
        results: List[SearchResult] = []
        for item in data.get("results", []):
            url = item.get("url", "")
            if not url:
                continue
            raw_engines = item.get("engines", [])
            try:
                score = _clamp_score(float(item.get("score", 1.0) or 1.0))
            except Exception:
                score = 1.0
            results.append(
                SearchResult(
                    url=url,
                    title=item.get("title", ""),
                    snippet=item.get("content", ""),
                    score=score,
                    raw={"engines": raw_engines, "source": "searxng"},
                )
            )
        return results, unresponsive

    @staticmethod
    def _unresponsive_map(unresponsive: list[Any]) -> dict[str, str]:
        out: dict[str, str] = {}
        for item in unresponsive:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                out[str(item[0]).strip().lower()] = str(item[1])
            elif isinstance(item, dict):
                name = item.get("engine") or item.get("name")
                reason = item.get("error") or item.get("reason") or item.get("message")
                if name and reason:
                    out[str(name).strip().lower()] = str(reason)
        return out

    def _update_breaker(self, attempted: List[str], unresponsive: list[Any], success_engines: set[str]) -> None:
        unresp_map = self._unresponsive_map(unresponsive)
        normalized_success = {s.strip().lower() for s in success_engines}
        for engine in attempted:
            normalized = engine.strip().lower()
            if normalized in unresp_map:
                err_type = classify_engine_error(unresp_map[normalized])
                self.breaker.record_failure(normalized, reason=f"{err_type}: {unresp_map[normalized][:120]}")
            elif normalized in normalized_success:
                self.breaker.record_success(normalized)

    async def _try_tier(self, query: str, limit: int, tier_engines: List[str], tier_name: str) -> List[SearchResult]:
        candidates = [e for e in tier_engines if e not in self.engines_disabled]
        available = self.breaker.filter_engines(candidates)
        if not available:
            logger.info("all engines in tier are circuit-open", tier=tier_name)
            return []
        logger.info("querying searxng tier", tier=tier_name, engines=available)
        try:
            results, unresponsive = await self._fetch(query, limit, available)
            success = {engine for result in results for engine in result.raw.get("engines", [])}
            self._update_breaker(available, unresponsive, success)
            return results
        except httpx.HTTPStatusError as exc:
            for engine in available:
                self.breaker.record_failure(engine, reason=f"transport: {repr(exc)[:120]}")
            mapped = self._map_http_error(exc)
            if isinstance(mapped, SearchRateLimited):
                raise mapped
            logger.warning("searxng tier http failed", tier=tier_name, error=repr(exc))
            return []
        except httpx.TimeoutException as exc:
            self._last_transport_error = exc
            logger.warning("searxng tier timeout", tier=tier_name, error=repr(exc))
            for engine in available:
                self.breaker.record_failure(engine, reason=f"transport: {repr(exc)[:120]}")
            return []
        except Exception as exc:
            logger.warning("searxng tier query failed", tier=tier_name, error=repr(exc))
            return []

    async def search(self, query: str, max_results: int = 10, engines: Optional[List[str]] = None) -> List[SearchResult]:
        if engines:
            requested = [e for e in engines if e not in self.engines_disabled]
            available = self.breaker.filter_engines(requested)
            if not available:
                raise SearchResultEmpty(f"Requested engines are circuit-open: {requested}")
            try:
                results, unresponsive = await self._fetch(query, max_results, available)
                success = {engine for result in results for engine in result.raw.get("engines", [])}
                self._update_breaker(available, unresponsive, success)
                if not results:
                    raise SearchResultEmpty(f"No results from engines {available} for query: '{query}'")
                return results[:max_results]
            except SearchResultEmpty:
                raise
            except httpx.HTTPStatusError as exc:
                raise self._map_http_error(exc)
            except httpx.TimeoutException as exc:
                msg = f"SearXNG request timeout: {repr(exc)}"
                logger.error("searxng timeout", error=repr(exc))
                raise SearchEngineUnavailable(msg)
            except Exception as exc:
                msg = f"SearXNG Connection Error: {repr(exc)}"
                logger.error("searxng connection error", error=repr(exc))
                raise SearchEngineUnavailable(msg)

        all_results: List[SearchResult] = []
        seen_urls: set[str] = set()
        self._last_transport_error = None
        for tier_name in ["tier1_stable", "tier2_knowledge", "tier3_academic", "tier4_general_api_trigger", "tier5_risky"]:
            tier_results = await self._try_tier(query, max_results, ENGINE_TIERS[tier_name], tier_name)
            for result in tier_results:
                key = result.url.split("#", 1)[0].rstrip("/").lower()
                if key in seen_urls:
                    continue
                seen_urls.add(key)
                all_results.append(result)
            if len(all_results) >= max_results or tier_results:
                break

        # Backward-compatible safety net for tests / older configs where the tier list is unsupported.
        if not all_results:
            logger.warning("all tiers empty; retrying legacy stable fallback pool")
            available = self.breaker.filter_engines(FALLBACK_ENGINE_POOL)
            if available:
                try:
                    results, unresponsive = await self._fetch(query, max_results, available)
                    success = {engine for result in results for engine in result.raw.get("engines", [])}
                    self._update_breaker(available, unresponsive, success)
                    all_results.extend(results)
                except Exception as exc:
                    logger.warning("legacy stable fallback failed", error=repr(exc))

        if not all_results:
            if isinstance(getattr(self, "_last_transport_error", None), httpx.TimeoutException):
                raise SearchEngineUnavailable(f"SearXNG request timeout: {repr(self._last_transport_error)}")
            raise SearchResultEmpty(
                f"All SearXNG engine tiers exhausted for query: '{query}'. Breaker: {self.breaker.snapshot()}"
            )
        all_results.sort(key=lambda r: r.score, reverse=True)
        return all_results[:max_results]

    def _map_http_error(self, exc: httpx.HTTPStatusError) -> Exception:
        status = exc.response.status_code
        text_lower = getattr(exc.response, "text", "").lower()
        if status in (429, 403) or "captcha" in text_lower or "unusual traffic" in text_lower:
            msg = f"SearXNG rate limited or CAPTCHA risk control triggered: {status}"
            logger.warning("searxng rate limited", status=status)
            return SearchRateLimited(msg)
        msg = f"SearXNG HTTP error: {status}"
        logger.error("searxng http error", status=status)
        return SearchEngineUnavailable(msg)

    async def health_check(self) -> bool:
        try:
            resp = await self.client.get("/search", params={"q": "ping", "format": "json", "limit": 1}, timeout=10.0)
            return resp.status_code == 200
        except Exception as exc:
            logger.warning("searxng health check failed", error=repr(exc))
            return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._client:
            await self._client.aclose()
            self._client = None

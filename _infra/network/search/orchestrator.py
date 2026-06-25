# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-25 00:00:00

"""
MultiSourceSearchOrchestrator - intent routing + tiered SearXNG + API fallback.

This orchestrator preserves the existing SearchProvider interface so callers can
continue to use `.search(query, max_results, engines)`. The fallback API layer is
optional and auto-loaded only when the corresponding environment variable exists.
"""

from __future__ import annotations

import os
import re
from typing import List, Optional

from _infra.network.core.secrets import load_local_env_files
from _infra.network.exceptions import SearchResultEmpty
from _infra.network.utils.logger import get_logger

from .base import SearchProvider
from .circuit_breaker import get_global_breaker
from .models import SearchResult
from .searxng_client import SearXNGProvider

logger = get_logger("network.search.orchestrator")

INTENT_PATTERNS = {
    "coding": [
        r"\b(python|javascript|typescript|rust|golang|go|java|c\+\+|swift)\b",
        r"\b(error|exception|traceback|stacktrace|compile|debug)\b",
        r"\b(api|sdk|library|framework|github|npm|pypi|cargo)\b",
        r"\b(import|from|def|class|function|async|await)\b",
        r"how to (use|implement|fix|install|configure)",
    ],
    "academic": [
        r"\b(paper|research|study|arxiv|doi|citation)\b",
        r"\b(algorithm|theorem|proof|hypothesis|methodology)\b",
        r"\b(neural network|deep learning|machine learning|transformer)\b",
        r"\b(20\d{2})\b.*\b(paper|research|publication)\b",
    ],
    "news": [
        r"\b(news|latest|update|release|announce|launch)\b",
        r"\b(today|yesterday|this week|breaking)\b",
    ],
}

INTENT_TO_ENGINES = {
    "coding": ["github", "stackoverflow", "lobste.rs", "mdn", "hackernews"],
    "academic": ["arxiv", "crossref", "pubmed", "semantic scholar", "wikipedia"],
    "news": ["hackernews", "lobste.rs"],
    "general": None,
}


def detect_intent(query: str) -> str:
    """Simple deterministic intent detector. Rules first; no LLM dependency."""
    q = query.lower()
    scores = {intent: 0 for intent in INTENT_PATTERNS}
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, q):
                scores[intent] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


class MultiSourceSearchOrchestrator(SearchProvider):
    """
    Top-level search orchestrator.

    Chain:
    L1. SearXNG intent route.
    L2. SearXNG tiered fallback route.
    L3. Optional API providers (Brave / Tavily / Serper) when keys exist.
    """

    def __init__(
        self,
        searxng: Optional[SearXNGProvider] = None,
        api_providers: Optional[List[SearchProvider]] = None,
        min_results_threshold: int = 3,
    ) -> None:
        self.searxng = searxng or SearXNGProvider()
        self.api_providers = api_providers if api_providers is not None else self._auto_load_api_providers()
        self.min_results_threshold = min_results_threshold

    def _auto_load_api_providers(self) -> List[SearchProvider]:
        load_local_env_files()
        providers: List[SearchProvider] = []
        if os.getenv("BRAVE_API_KEY"):
            try:
                from .api_providers import BraveSearchAPIProvider

                providers.append(BraveSearchAPIProvider())
                logger.info("loaded brave api fallback")
            except Exception as exc:
                logger.warning("brave api provider init failed", error=repr(exc))
        if os.getenv("TAVILY_API_KEY"):
            try:
                from .api_providers import TavilySearchAPIProvider

                providers.append(TavilySearchAPIProvider())
                logger.info("loaded tavily api fallback")
            except Exception as exc:
                logger.warning("tavily api provider init failed", error=repr(exc))
        if os.getenv("SERPER_API_KEY"):
            try:
                from .api_providers import SerperAPIProvider

                providers.append(SerperAPIProvider())
                logger.info("loaded serper api fallback")
            except Exception as exc:
                logger.warning("serper api provider init failed", error=repr(exc))
        return providers

    @staticmethod
    def _dedupe(results: List[SearchResult]) -> List[SearchResult]:
        seen: set[str] = set()
        out: List[SearchResult] = []
        for result in results:
            key = result.url.split("#", 1)[0].rstrip("/").lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(result)
        return out

    async def search(
        self,
        query: str,
        max_results: int = 10,
        engines: Optional[List[str]] = None,
        mode: str = "auto",
    ) -> List[SearchResult]:
        # Explicit engine requests are respected: caller is asking SearXNG only.
        if engines:
            return await self.searxng.search(query, max_results=max_results, engines=engines)

        intent = detect_intent(query) if mode == "auto" else mode
        logger.info("search orchestrator route", intent=intent, query=query[:120])

        all_results: List[SearchResult] = []

        # L1: intent-specific SearXNG route.
        try:
            intent_engines = INTENT_TO_ENGINES.get(intent)
            if intent_engines:
                results = await self.searxng.search(query, max_results=max_results, engines=intent_engines)
            else:
                results = await self.searxng.search(query, max_results=max_results, engines=None)
            all_results.extend(results)
            logger.info("L1 searxng route returned", count=len(results), intent=intent)
        except SearchResultEmpty:
            logger.warning("L1 searxng route empty", intent=intent)
        except Exception as exc:
            logger.warning("L1 searxng route failed", intent=intent, error=repr(exc))

        # L2: full SearXNG tier fallback if L1 insufficient.
        if len(self._dedupe(all_results)) < self.min_results_threshold:
            try:
                results = await self.searxng.search(query, max_results=max_results, engines=None)
                all_results.extend(results)
                logger.info("L2 searxng tier returned", count=len(results))
            except SearchResultEmpty:
                logger.warning("L2 searxng tier empty")
            except Exception as exc:
                logger.warning("L2 searxng tier failed", error=repr(exc))

        # L3: optional API fallback when configured by env vars.
        if len(self._dedupe(all_results)) < self.min_results_threshold:
            for provider in self.api_providers:
                try:
                    results = await provider.search(query, max_results=max_results)
                    all_results.extend(results)
                    logger.info("L3 api fallback returned", provider=provider.get_name(), count=len(results))
                    if len(self._dedupe(all_results)) >= self.min_results_threshold:
                        break
                except Exception as exc:
                    logger.warning("L3 api fallback failed", provider=provider.get_name(), error=repr(exc))

        deduped = self._dedupe(all_results)
        deduped.sort(key=lambda r: r.score, reverse=True)
        if not deduped:
            raise SearchResultEmpty(
                f"All search sources exhausted for query: '{query}'. Breaker: {get_global_breaker().snapshot()}"
            )
        return deduped[:max_results]

    async def health_check(self) -> bool:
        status = await self.health_status()
        return bool(status.get("searxng")) or any(status.get("api_providers", {}).values())

    async def health_status(self) -> dict:
        return {
            "searxng": await self.searxng.health_check(),
            "api_providers": {p.get_name(): await p.health_check() for p in self.api_providers},
            "circuit_breaker": get_global_breaker().snapshot(),
        }

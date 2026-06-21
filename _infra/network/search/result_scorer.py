"""
Domain Reputation Scorer (FORGE Network incremental)

Task: E3-C3-S1-T2

Per TASK_BACKLOG + NETWORK_ENGINEERING_DESIGN §6.2

- Configuration driven (domain_reputation.yaml)
- Positive boost: github, arxiv, edu, wikipedia, official docs
- Negative penalty: SEO spam, AI-generated low-quality
- Score range: 0.0 - 1.0 (base 0.5)
- Can be used to re-rank SearchResult list
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import yaml

from _infra.network.search.models import SearchResult


DEFAULT_CONFIG = {
    "positive": {
        "github.com": 0.25,
        "arxiv.org": 0.30,
        "wikipedia.org": 0.20,
        "*.edu": 0.18,
        "docs.python.org": 0.22,
        "developer.mozilla.org": 0.20,
        "stackoverflow.com": 0.15,
    },
    "negative": {
        "clickbait.com": -0.30,
        "spammy-seo.net": -0.35,
        "low-quality-ai.com": -0.25,
        "example-spam.org": -0.40,
    },
    "default_score": 0.50,
}


def load_domain_reputation_config(
    path: Optional[Path] = None,
) -> dict:
    """Load domain reputation config. Falls back to defaults."""
    if path is None:
        # Try project-relative config
        candidate = Path("config") / "domain_reputation.yaml"
        if candidate.exists():
            path = candidate
        else:
            return DEFAULT_CONFIG

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        # merge with defaults
        cfg = DEFAULT_CONFIG.copy()
        cfg.update(data.get("domain_reputation", data) or {})
        return cfg
    except Exception:
        return DEFAULT_CONFIG


def score_domain(domain: str, config: Optional[dict] = None) -> float:
    """
    Return reputation score for a domain (0.0-1.0).
    """
    if config is None:
        config = load_domain_reputation_config()

    domain = domain.lower().strip()
    if not domain:
        return config.get("default_score", 0.5)

    # exact match positive
    pos = config.get("positive", {})
    if domain in pos:
        return min(1.0, max(0.0, 0.5 + pos[domain]))

    # wildcard *.edu style
    for pat, boost in pos.items():
        if pat.startswith("*.") and domain.endswith(pat[1:]):
            return min(1.0, max(0.0, 0.5 + boost))

    # negative
    neg = config.get("negative", {})
    for bad, penalty in neg.items():
        if bad in domain or domain.endswith(bad):
            return min(1.0, max(0.0, 0.5 + penalty))

    return config.get("default_score", 0.5)


def rank_search_results(
    results: List[SearchResult],
    config: Optional[dict] = None,
) -> List[SearchResult]:
    """
    Re-score and sort results in-place by combined (original + domain) score.
    """
    if not results:
        return results

    if config is None:
        config = load_domain_reputation_config()

    for r in results:
        domain_score = score_domain(r.domain, config)
        # Blend: 60% original + 40% domain reputation (conservative)
        r.score = round(0.6 * r.score + 0.4 * domain_score, 4)

    # Re-sort descending
    results.sort(key=lambda r: r.score, reverse=True)
    return results

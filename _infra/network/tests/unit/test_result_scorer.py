"""
Unit tests for Domain Reputation Scorer (E3-C3-S1-T2)
"""

import pytest

from _infra.network.search.models import SearchResult
from _infra.network.search.result_scorer import (
    load_domain_reputation_config,
    rank_search_results,
    score_domain,
)


def test_score_high_reputation():
    assert score_domain("github.com") > 0.7
    assert score_domain("arxiv.org") > 0.75
    assert score_domain("wikipedia.org") > 0.65


def test_score_edu_wildcard():
    assert score_domain("mit.edu") > 0.6
    assert score_domain("stanford.edu") > 0.6


def test_score_negative_spam():
    score = score_domain("spammy-seo.net")
    assert score < 0.3


def test_default_score():
    assert 0.4 < score_domain("random-blog.com") < 0.6


def test_rank_search_results():
    results = [
        SearchResult(url="https://spammy-seo.net/1", title="Spam", score=0.9),
        SearchResult(url="https://github.com/python", title="Python", score=0.6),
        SearchResult(url="https://random.com", title="Random", score=0.5),
    ]

    ranked = rank_search_results(results)

    # github should now be highest
    assert ranked[0].domain == "github.com"
    assert ranked[0].score > 0.7
    assert ranked[-1].score < 0.4  # spam should be low


def test_config_load_fallback():
    cfg = load_domain_reputation_config()
    assert "positive" in cfg
    assert "github.com" in cfg["positive"]

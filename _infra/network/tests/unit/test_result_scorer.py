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

    # github should now be highest after domain boost
    assert ranked[0].domain == "github.com"
    # blended: 0.6*0.6 + 0.4*(0.5+0.25) ≈ 0.66
    assert ranked[0].score > 0.60

    # spam ends up with blended score < 0.7 (from high original 0.9 + negative domain)
    spam_scores = [r.score for r in ranked if "spammy" in r.domain]
    assert spam_scores and spam_scores[0] < 0.65

    # random stays around its input
    random_scores = [r.score for r in ranked if "random" in r.domain]
    assert random_scores and 0.48 < random_scores[0] < 0.52


def test_config_load_fallback():
    cfg = load_domain_reputation_config()
    assert "positive" in cfg
    assert "github.com" in cfg["positive"]

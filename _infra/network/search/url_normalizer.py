"""
URL Normalizer (FORGE Network incremental)

Task: E3-C3-S1-T1

Per TASK_BACKLOG + NETWORK_ENGINEERING_DESIGN §5.3 / §6.2

- Remove tracking params (utm_*, fbclid, gclid, ref, etc.)
- Force https scheme
- Remove trailing slash (except root)
- Lowercase hostname
- Return canonical form for deduping / scoring
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "ref",
    "source",
    "mc_cid",
    "mc_eid",
    "yclid",
    "dclid",
    "_ga",
    "_gl",
    "spm",
    "from",
    "igshid",
}


def normalize_url(url: str) -> str:
    """
    Normalize a URL for deduplication and scoring.

    Returns a canonical string.
    """
    if not url or not isinstance(url, str):
        raise ValueError("url must be non-empty string")

    try:
        parsed = urlparse(url.strip())
    except Exception:
        return url  # fallback to original if unparsable

    if not parsed.scheme or not parsed.netloc:
        return url

    # Force https
    scheme = "https"

    # Lower hostname
    netloc = parsed.netloc.lower()

    # Remove default ports
    if netloc.endswith(":80"):
        netloc = netloc[:-3]
    if netloc.endswith(":443"):
        netloc = netloc[:-4]

    # Clean query: remove tracking params
    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    clean_pairs = [
        (k, v)
        for k, v in query_pairs
        if k.lower() not in TRACKING_PARAMS
    ]
    clean_query = urlencode(clean_pairs)

    # Path: strip trailing slash unless root
    path = parsed.path.rstrip("/")
    if not path:
        path = "/"

    # Rebuild
    normalized = urlunparse((
        scheme,
        netloc,
        path,
        parsed.params,
        clean_query,
        "",  # no fragment
    ))

    return normalized


def is_same_url(url1: str, url2: str) -> bool:
    """Return True if two URLs normalize to the same canonical form."""
    return normalize_url(url1) == normalize_url(url2)

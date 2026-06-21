"""
Unicode Normalization utilities (FORGE Network incremental)

E5-C2-S1-T1: Unicode 预处理

Implements:
- NFKC normalization (full-width → half-width, compatibility)
- Removal of zero-width characters (U+200B–U+200D, U+FEFF, etc.)
- URL percent-decoding
- Optional Base64 detection & decode (conservative, only if looks like Base64 PII)

Per TASK_BACKLOG E5-C2-S1-T1 + NETWORK_ENGINEERING_DESIGN §10.4
"""

from __future__ import annotations

import base64
import re
import unicodedata
from urllib.parse import unquote

from _infra.network.utils.logger import get_logger

logger = get_logger("network.utils.unicode_norm")


# Zero-width and invisible characters to strip
ZERO_WIDTH_CHARS = {
    "\u200b",  # ZERO WIDTH SPACE
    "\u200c",  # ZERO WIDTH NON-JOINER
    "\u200d",  # ZERO WIDTH JOINER
    "\ufeff",  # ZERO WIDTH NO-BREAK SPACE (BOM)
    "\u2060",  # WORD JOINER
    "\u180e",  # MONGOLIAN VOWEL SEPARATOR (historical)
    "\u200e",  # LEFT-TO-RIGHT MARK
    "\u200f",  # RIGHT-TO-LEFT MARK
}


def normalize_unicode(text: str, decode_url: bool = True, try_base64: bool = False) -> str:
    """
    Full Unicode normalization pipeline.

    Steps (in order):
    1. URL percent-decode (if enabled)
    2. NFKC normalization (full-width → half-width, compatibility forms)
    3. Remove zero-width / invisible characters
    4. (Optional) Base64 decode if text looks like a Base64-encoded string

    Returns cleaned string.
    """
    if not text or not isinstance(text, str):
        return ""

    result = text

    # 1. URL decoding (handles % encodings that may hide characters)
    if decode_url:
        try:
            # Decode multiple times in case of double-encoding (safe)
            for _ in range(2):
                decoded = unquote(result)
                if decoded == result:
                    break
                result = decoded
        except Exception:
            pass  # keep original if decode fails

    # 2. NFKC normalization (most important for Chinese/ full-width)
    try:
        result = unicodedata.normalize("NFKC", result)
    except Exception:
        pass

    # 3. Remove zero-width characters
    result = "".join(ch for ch in result if ch not in ZERO_WIDTH_CHARS)

    # 4. Optional Base64 decode (only if it looks like a plausible encoded string)
    if try_base64 and _looks_like_base64(result):
        try:
            # Try decode (must be valid padding etc.)
            decoded_bytes = base64.b64decode(result, validate=True)
            decoded_str = decoded_bytes.decode("utf-8", errors="replace")
            # Only accept if result is significantly different and printable
            if decoded_str and len(decoded_str) > 3 and decoded_str.isprintable():
                logger.debug("Base64 decoded in unicode norm")
                result = decoded_str
        except Exception:
            pass  # not valid Base64 or not UTF-8 → keep original

    # Final whitespace normalization
    result = re.sub(r"\s+", " ", result).strip()

    return result


def _looks_like_base64(s: str) -> bool:
    """Heuristic: looks like Base64 (alphanum + /+ = padding, length multiple of 4)."""
    if len(s) < 8 or len(s) % 4 != 0:
        return False
    # Must contain only valid Base64 chars (allow = padding)
    if not re.match(r"^[A-Za-z0-9+/]+={0,2}$", s):
        return False
    return True  # when caller explicitly asks for try_base64, be permissive


def normalize_for_pii_detection(text: str) -> str:
    """
    Stronger normalization specifically tuned for PII / injection detection.
    Applies URL decode + NFKC + zero-width removal.
    """
    return normalize_unicode(text, decode_url=True, try_base64=False)


# Convenience alias used by many callers
normalize = normalize_unicode

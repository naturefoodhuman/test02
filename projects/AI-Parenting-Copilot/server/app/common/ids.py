# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 22:55:00


"""ULID helpers.

ULIDs keep identifiers sortable while remaining globally unique across Android,
Mac server and future device adapters.
"""
from __future__ import annotations

import re

from ulid import ULID

ULID_RE = re.compile(r"^[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{26}$")


def new_ulid() -> str:
    """Return a new canonical Crockford Base32 ULID string."""

    return str(ULID())


def is_ulid(value: str) -> bool:
    """Return True when `value` is a syntactically valid ULID."""

    if not ULID_RE.fullmatch(value):
        return False
    try:
        ULID.from_str(value)
    except ValueError:
        return False
    return True

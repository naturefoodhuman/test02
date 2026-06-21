"""
SearchCache (FORGE Network incremental)

E3-C4-S1-T1

SQLite-based LRU cache for search results.
- TTL (default 1h)
- Max size (default 1000)
- Key = sha256(query + max_results + language)
- Stores serialized SearchResult list

Per TASK_BACKLOG + NETWORK_ENGINEERING_DESIGN §11.2
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import List, Optional

from _infra.network.config_loader import load_network_config
from _infra.network.utils.logger import get_logger

from .models import SearchResult

logger = get_logger("network.search.cache")


class SearchCache:
    """
    Lightweight SQLite LRU cache for search results.
    Thread-safe enough for single-process use.
    """

    def __init__(
        self,
        db_path: str | Path = "runtime/search_cache.db",
        max_size: int = 1000,
        default_ttl: int = 3600,
    ):
        self.db_path = Path(db_path)
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS search_cache (
                key TEXT PRIMARY KEY,
                results_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON search_cache(expires_at)")
        conn.commit()

    def _make_key(self, query: str, max_results: int, language: str = "zh") -> str:
        raw = f"{query}|{max_results}|{language}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def get(
        self,
        query: str,
        max_results: int = 20,
        language: str = "zh",
    ) -> Optional[List[SearchResult]]:
        key = self._make_key(query, max_results, language)
        conn = self._get_conn()

        row = conn.execute(
            "SELECT results_json, expires_at FROM search_cache WHERE key = ?",
            (key,),
        ).fetchone()

        if not row:
            return None

        if time.time() > row["expires_at"]:
            # expired
            conn.execute("DELETE FROM search_cache WHERE key = ?", (key,))
            conn.commit()
            return None

        try:
            data = json.loads(row["results_json"])
            results = [SearchResult(**item) for item in data]
            return results
        except Exception as e:
            logger.warning("cache deserialization failed", error=str(e))
            return None

    def set(
        self,
        query: str,
        results: List[SearchResult],
        max_results: int = 20,
        language: str = "zh",
        ttl: Optional[int] = None,
    ) -> None:
        if not results:
            return

        key = self._make_key(query, max_results, language)
        ttl = ttl or self.default_ttl
        now = time.time()
        expires = now + ttl

        payload = json.dumps([r.model_dump() for r in results], ensure_ascii=False)

        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO search_cache (key, results_json, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (key, payload, now, expires),
        )

        # LRU eviction (simple: delete oldest when over limit)
        count = conn.execute("SELECT COUNT(*) FROM search_cache").fetchone()[0]
        if count > self.max_size:
            to_delete = count - self.max_size
            conn.execute(
                """
                DELETE FROM search_cache
                WHERE key IN (
                    SELECT key FROM search_cache
                    ORDER BY created_at ASC
                    LIMIT ?
                )
                """,
                (to_delete,),
            )

        conn.commit()

    def clear_expired(self) -> int:
        conn = self._get_conn()
        now = time.time()
        cur = conn.execute("DELETE FROM search_cache WHERE expires_at < ?", (now,))
        conn.commit()
        return cur.rowcount

    def clear_all(self) -> None:
        conn = self._get_conn()
        conn.execute("DELETE FROM search_cache")
        conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


# Convenience factory
def get_search_cache() -> SearchCache:
    """Factory using config if available (falls back to defaults)."""
    try:
        cfg = load_network_config()
        # Could extend config later; for now use sane defaults
        return SearchCache(
            db_path="runtime/search_cache.db",
            max_size=1000,
            default_ttl=3600,
        )
    except Exception:
        return SearchCache()

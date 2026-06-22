# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 20:32:00

"""
PII Map DB — encrypted placeholder mapping store (E5-C6-S1-T2).

Per NETWORK_ENGINEERING_DESIGN.md §6.1 and TASK_BACKLOG E5-C6-S1-T2.

Production intent:
- Prefer SQLCipher when a compatible Python driver is installed
  (``sqlcipher3`` or ``pysqlcipher3``).
- Store each original value as an authenticated AES-256-CBC encrypted BLOB.

Minimal-environment behavior:
- The current sandbox does not ship SQLCipher Python bindings. To keep unit
  tests deterministic while preserving confidentiality of ``original`` values,
  this module can fall back to stdlib sqlite3 with field-level AES-256
  encryption. Set ``require_sqlcipher=True`` to fail fast when SQLCipher is not
  available.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
from typing import Mapping, Optional

from .models import PIIType
from .replacer import PIIPlaceholderMapping

MAGIC = b"PMAP2"
SALT_LEN = 16
IV_LEN = 16
TAG_LEN = 32
PBKDF2_ITERATIONS = 200_000

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS pii_mappings (
    id           TEXT NOT NULL,
    placeholder  TEXT NOT NULL,
    entity_type  TEXT NOT NULL,
    original     BLOB NOT NULL,
    recognizer   TEXT NOT NULL DEFAULT 'unknown',
    score        REAL NOT NULL DEFAULT 0.0,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at   TEXT,
    PRIMARY KEY (id, placeholder)
);

CREATE INDEX IF NOT EXISTS idx_pii_placeholder ON pii_mappings(placeholder);
CREATE INDEX IF NOT EXISTS idx_pii_mapping_id ON pii_mappings(id);
"""


class PIIMapDBError(Exception):
    """Base error for encrypted PII map DB."""


class PIIMapDBUnavailableError(PIIMapDBError):
    """Raised when required crypto / SQLCipher backend is unavailable."""


class PIIMapDecryptionError(PIIMapDBError):
    """Raised when a mapping cannot be decrypted, usually due to wrong key."""


@dataclass(frozen=True)
class PIIMapDBConfig:
    """Configuration for PIIMapDB."""

    db_path: Path
    encryption_key: str
    require_sqlcipher: bool = False


class AES256FieldCipher:
    """Authenticated AES-256-CBC field encryption using the OpenSSL CLI."""

    def __init__(self, secret: str):
        if len(secret) < 16:
            raise PIIMapDBUnavailableError("PII_MAP_ENCRYPTION_KEY must be at least 16 characters")
        if shutil.which("openssl") is None:
            raise PIIMapDBUnavailableError("openssl command not found; cannot encrypt PII mapping blobs")
        self.secret = secret.encode("utf-8")

    @staticmethod
    def _derive_keys(secret: bytes, salt: bytes) -> tuple[bytes, bytes]:
        material = hashlib.pbkdf2_hmac(
            "sha256",
            secret,
            salt,
            PBKDF2_ITERATIONS,
            dklen=64,
        )
        return material[:32], material[32:]

    @staticmethod
    def _openssl_aes_cbc(data: bytes, aes_key: bytes, iv: bytes, decrypt: bool = False) -> bytes:
        cmd = [
            "openssl",
            "enc",
            "-aes-256-cbc",
            "-K",
            aes_key.hex(),
            "-iv",
            iv.hex(),
            "-nosalt",
        ]
        if decrypt:
            cmd.insert(2, "-d")

        proc = subprocess.run(
            cmd,
            input=data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            raise PIIMapDecryptionError(proc.stderr.decode("utf-8", errors="ignore") or "openssl failed")
        return proc.stdout

    @staticmethod
    def _tag(mac_key: bytes, salt: bytes, iv: bytes, ciphertext: bytes) -> bytes:
        return hmac.new(mac_key, MAGIC + salt + iv + ciphertext, hashlib.sha256).digest()

    def encrypt(self, plaintext: str) -> bytes:
        salt = os.urandom(SALT_LEN)
        iv = os.urandom(IV_LEN)
        aes_key, mac_key = self._derive_keys(self.secret, salt)
        ciphertext = self._openssl_aes_cbc(plaintext.encode("utf-8"), aes_key, iv, decrypt=False)
        tag = self._tag(mac_key, salt, iv, ciphertext)
        return MAGIC + salt + iv + tag + ciphertext

    def decrypt(self, blob: bytes) -> str:
        if len(blob) <= len(MAGIC) + SALT_LEN + IV_LEN + TAG_LEN:
            raise PIIMapDecryptionError("encrypted blob is too short")
        if not blob.startswith(MAGIC):
            raise PIIMapDecryptionError("invalid encrypted blob header")

        offset = len(MAGIC)
        salt = blob[offset : offset + SALT_LEN]
        offset += SALT_LEN
        iv = blob[offset : offset + IV_LEN]
        offset += IV_LEN
        expected_tag = blob[offset : offset + TAG_LEN]
        offset += TAG_LEN
        ciphertext = blob[offset:]

        aes_key, mac_key = self._derive_keys(self.secret, salt)
        actual_tag = self._tag(mac_key, salt, iv, ciphertext)
        if not hmac.compare_digest(expected_tag, actual_tag):
            raise PIIMapDecryptionError("PII mapping decryption failed: authentication tag mismatch")

        plaintext = self._openssl_aes_cbc(ciphertext, aes_key, iv, decrypt=True)
        return plaintext.decode("utf-8")


class PIIMapDB:
    """Encrypted SQLite / SQLCipher-backed mapping store for PIIReplacer."""

    def __init__(
        self,
        db_path: str | Path,
        encryption_key: str,
        require_sqlcipher: bool = False,
    ):
        self.db_path = Path(db_path)
        self.encryption_key = encryption_key
        self.require_sqlcipher = require_sqlcipher
        self.cipher = AES256FieldCipher(encryption_key)
        self._dbapi, self.driver_name = self._load_dbapi(require_sqlcipher=require_sqlcipher)
        self.init_db()

    @staticmethod
    def _load_dbapi(require_sqlcipher: bool = False):
        try:
            import sqlcipher3  # type: ignore

            return sqlcipher3, "sqlcipher3"
        except ImportError:
            try:
                from pysqlcipher3 import dbapi2 as pysqlcipher3_dbapi  # type: ignore

                return pysqlcipher3_dbapi, "pysqlcipher3"
            except ImportError:
                if require_sqlcipher:
                    raise PIIMapDBUnavailableError(
                        "SQLCipher Python driver not installed. Install sqlcipher3-binary or pysqlcipher3."
                    )
                return sqlite3, "sqlite3-field-encrypted-fallback"

    def _connect(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._dbapi.connect(str(self.db_path))
        if self.driver_name in {"sqlcipher3", "pysqlcipher3"}:
            escaped_key = self.encryption_key.replace("'", "''")
            conn.execute(f"PRAGMA key = '{escaped_key}'")
        return conn

    def init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    def save(self, mapping_id: str, mapping: Mapping[str, PIIPlaceholderMapping]) -> None:
        """Persist a complete placeholder mapping, replacing any old rows."""
        with self._connect() as conn:
            conn.execute("DELETE FROM pii_mappings WHERE id = ?", (mapping_id,))
            for placeholder, entry in mapping.items():
                conn.execute(
                    """
                    INSERT INTO pii_mappings
                        (id, placeholder, entity_type, original, recognizer, score, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, NULL)
                    """,
                    (
                        mapping_id,
                        placeholder,
                        entry.type.value,
                        self.cipher.encrypt(entry.value),
                        entry.recognizer,
                        float(entry.score),
                    ),
                )
            conn.commit()

    def get(self, mapping_id: str) -> dict[str, PIIPlaceholderMapping]:
        """Return decrypted mapping for mapping_id."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT placeholder, entity_type, original, recognizer, score
                FROM pii_mappings
                WHERE id = ?
                ORDER BY placeholder
                """,
                (mapping_id,),
            ).fetchall()

        result: dict[str, PIIPlaceholderMapping] = {}
        for placeholder, entity_type, original, recognizer, score in rows:
            value = self.cipher.decrypt(bytes(original))
            result[placeholder] = PIIPlaceholderMapping(
                placeholder=placeholder,
                type=PIIType(entity_type),
                value=value,
                recognizer=recognizer,
                score=float(score),
            )
        return result

    def has(self, mapping_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM pii_mappings WHERE id = ? LIMIT 1",
                (mapping_id,),
            ).fetchone()
        return row is not None

    def get_original(self, mapping_id: str, placeholder: str) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT original FROM pii_mappings WHERE id = ? AND placeholder = ?",
                (mapping_id, placeholder),
            ).fetchone()
        if row is None:
            return None
        return self.cipher.decrypt(bytes(row[0]))

    def delete(self, mapping_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM pii_mappings WHERE id = ?", (mapping_id,))
            conn.commit()

    @classmethod
    def from_env(
        cls,
        db_path: str | Path = "runtime/pii_map.db",
        require_sqlcipher: bool = False,
    ) -> "PIIMapDB":
        from ..core.secrets import get_pii_encryption_key

        return cls(
            db_path=db_path,
            encryption_key=get_pii_encryption_key(),
            require_sqlcipher=require_sqlcipher,
        )


__all__ = [
    "AES256FieldCipher",
    "PIIMapDB",
    "PIIMapDBConfig",
    "PIIMapDBError",
    "PIIMapDBUnavailableError",
    "PIIMapDecryptionError",
    "SCHEMA_SQL",
]

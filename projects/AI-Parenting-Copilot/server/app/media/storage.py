# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 08:40:00


"""Encrypted local media storage service."""

from __future__ import annotations

import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pydantic import BaseModel, Field

from server.app.common.clock import utc_now
from server.app.common.ids import new_ulid


class MediaAssetRecord(BaseModel):
    id: str = Field(default_factory=new_ulid)
    family_id: str
    baby_id: str | None = None
    event_id: str | None = None
    filename: str
    content_type: str
    local_path: str
    thumbnail_path: str | None = None
    encrypted: bool = True
    tags: dict[str, object] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class MediaStorageService:
    """AES-GCM encrypted file store.

    DB media_asset persistence is a later repository task; this service keeps file
    encryption/decryption testable with in-memory records.
    """

    def __init__(self, *, root: Path | str = "runtime/media", key: bytes | None = None) -> None:
        self.root = Path(root)
        self.files_dir = self.root / "files"
        self.thumbs_dir = self.root / "thumbs"
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self.thumbs_dir.mkdir(parents=True, exist_ok=True)
        self.key = key or AESGCM.generate_key(bit_length=256)
        self.assets: dict[str, MediaAssetRecord] = {}

    @classmethod
    def from_base64_key(cls, *, root: Path | str, key_b64: str | None) -> MediaStorageService:
        key = base64.urlsafe_b64decode(key_b64.encode()) if key_b64 else None
        return cls(root=root, key=key)

    def store(
        self,
        *,
        content: bytes,
        filename: str,
        content_type: str,
        family_id: str,
        baby_id: str | None = None,
        event_id: str | None = None,
        tags: dict[str, object] | None = None,
    ) -> MediaAssetRecord:
        asset_id = new_ulid()
        nonce = os.urandom(12)
        encrypted = nonce + AESGCM(self.key).encrypt(nonce, content, None)
        path = self.files_dir / f"{asset_id}.bin"
        path.write_bytes(encrypted)
        record = MediaAssetRecord(
            id=asset_id,
            family_id=family_id,
            baby_id=baby_id,
            event_id=event_id,
            filename=filename,
            content_type=content_type,
            local_path=str(path),
            tags=dict(tags or {}),
        )
        self.assets[record.id] = record
        return record

    def read(self, asset_id: str) -> bytes:
        record = self.assets[asset_id]
        encrypted = Path(record.local_path).read_bytes()
        nonce, ciphertext = encrypted[:12], encrypted[12:]
        return AESGCM(self.key).decrypt(nonce, ciphertext, None)

    def attach_thumbnail(self, asset_id: str, thumbnail_path: str) -> MediaAssetRecord:
        record = self.assets[asset_id]
        record.thumbnail_path = thumbnail_path
        return record

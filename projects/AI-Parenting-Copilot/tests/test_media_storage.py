# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 08:40:00

"""APC-T042 media storage tests."""

from __future__ import annotations

import base64
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from server.app.main import create_app
from server.app.media.storage import MediaStorageService
from server.app.media.thumbnails import generate_thumbnail
from server.app.settings import Settings


def _png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (4, 4), color="red").save(buffer, format="PNG")
    return buffer.getvalue()


def test_media_storage_encrypt_decrypt_roundtrip(tmp_path) -> None:  # type: ignore[no-untyped-def]
    service = MediaStorageService(root=tmp_path)
    content = b"private baby photo bytes"

    record = service.store(
        content=content,
        filename="photo.bin",
        content_type="application/octet-stream",
        family_id="family-1",
    )

    assert record.encrypted is True
    assert content not in __import__("pathlib").Path(record.local_path).read_bytes()
    assert service.read(record.id) == content


def test_thumbnail_generation(tmp_path) -> None:  # type: ignore[no-untyped-def]
    thumb = generate_thumbnail(_png_bytes(), tmp_path / "thumb.png")

    assert thumb.exists()
    assert thumb.read_bytes().startswith(b"\x89PNG")


def test_media_upload_and_read_api() -> None:
    app = create_app(Settings(env="test"))
    content = _png_bytes()
    with TestClient(app) as client:
        uploaded = client.post(
            "/api/v1/media",
            json={
                "family_id": "family-1",
                "filename": "photo.png",
                "content_type": "image/png",
                "content_base64": base64.b64encode(content).decode(),
            },
        )
        assert uploaded.status_code == 200
        asset = uploaded.json()
        assert asset["thumbnail_path"]

        downloaded = client.get(f"/api/v1/media/{asset['id']}")
        assert downloaded.status_code == 200
        assert downloaded.content == content

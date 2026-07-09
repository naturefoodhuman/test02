# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 08:40:00


"""Thumbnail generation helpers."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image


def generate_thumbnail(
    image_bytes: bytes,
    output_path: Path,
    *,
    size: tuple[int, int] = (128, 128),
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(BytesIO(image_bytes)) as image:
        image.thumbnail(size)
        image.save(output_path, format="PNG")
    return output_path

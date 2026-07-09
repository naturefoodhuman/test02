# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 07:15:00


"""RTSP client abstraction with dev mock snapshot support."""

from __future__ import annotations

import base64

# 1x1 transparent PNG.
MOCK_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


class MockRTSPSnapshotClient:
    def __init__(self, camera_id: str = "nursery") -> None:
        self.camera_id = camera_id

    async def snapshot(self) -> bytes:
        return MOCK_PNG_BYTES

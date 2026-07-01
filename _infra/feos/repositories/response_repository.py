# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Response artifact repository wrapper."""

from __future__ import annotations

from .artifact_repository import ArtifactRepository


class ResponseRepository(ArtifactRepository):
    def __init__(self, workspace):
        super().__init__(workspace, "response")

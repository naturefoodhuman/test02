# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import pytest

from _infra.feos.repositories import ArtifactRepository
from _infra.feos.storage import FEOSWorkspace, sha256_text


def test_artifact_repository_yaml_json_text_raw(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos")
    ws.ensure_initialized()
    repo = ArtifactRepository(ws, "evidence")
    repo.put_yaml("case_001", "ev_001", {"id": "ev_001"})
    repo.put_json("case_001", "idx", {"items": ["ev_001"]})
    repo.put_text("case_001", "note", "hello", ".md")
    raw = repo.put_raw("case_001", "raw", b"secret", ".txt")

    assert repo.get_yaml("case_001", "ev_001") == {"id": "ev_001"}
    assert repo.get_json("case_001", "idx") == {"items": ["ev_001"]}
    assert raw.hash == sha256_text("secret")
    assert len(repo.list_paths("case_001")) == 4


def test_artifact_repository_rejects_path_traversal(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos")
    ws.ensure_initialized()
    repo = ArtifactRepository(ws, "evidence")
    with pytest.raises(ValueError):
        repo.put_yaml("case_001", "../bad", {})

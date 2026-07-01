# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.ingestion import ResponseIngestionService
from _infra.feos.repositories import ResponseRepository
from _infra.feos.storage import FEOSWorkspace


def test_import_response_saves_raw_and_metadata(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos"); ws.ensure_initialized()
    response = ResponseIngestionService(ResponseRepository(ws)).import_text("case", "## Root Cause\nMismatch", session_id="session")
    assert response.content_hash.startswith("sha256:")
    assert (ws.root / response.raw_ref).exists()
    assert (ws.root / "cases" / "case" / "response" / f"{response.id}.yaml").exists()

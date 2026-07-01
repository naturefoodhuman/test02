# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import pytest

from _infra.feos.errors import FEOSStorageError
from _infra.feos.storage import FEOSWorkspace, PathGuard


def test_workspace_initialization_and_case_dir(tmp_path):
    ws = FEOSWorkspace(tmp_path / ".forge" / "feos")
    ws.ensure_initialized()
    for item in FEOSWorkspace.REQUIRED_DIRS:
        assert (ws.root / item).is_dir()
    assert ws.case_dir("case_2026_07_01_001") == ws.root / "cases" / "case_2026_07_01_001"


def test_path_guard_rejects_escape_and_absolute(tmp_path):
    guard = PathGuard(tmp_path)
    with pytest.raises(FEOSStorageError):
        guard.resolve("../outside")
    with pytest.raises(FEOSStorageError):
        guard.resolve("/tmp/outside")


def test_workspace_rejects_bad_case_id(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos")
    with pytest.raises(ValueError):
        ws.case_dir("../bad")

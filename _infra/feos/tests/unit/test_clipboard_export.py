# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import pytest

from _infra.feos.errors import FEOSPolicyError
from _infra.feos.gateways import ClipboardGateway
from _infra.feos.models import EscalationPackage
from _infra.feos.policy import PolicyResult
from _infra.feos.storage import FEOSWorkspace, read_json


def test_clipboard_export_files(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos"); ws.ensure_initialized()
    gateway = ClipboardGateway(ws)
    pkg = EscalationPackage(id="pkg_001", case_id="case_001", context_package_id="ctx_001")
    result = gateway.prepare(pkg, "secret", PolicyResult(allowed=True, redacted_text="redacted", redaction_report={"count": 1}))
    export_dir = ws.root / "cases" / "case_001" / "exports"
    assert (export_dir / "clipboard.md").read_text() == "redacted"
    assert (export_dir / "package.json").exists()
    assert read_json(export_dir / "audit.json")["content_hash"] == result["content_hash"]


def test_clipboard_export_blocked_by_policy(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos"); ws.ensure_initialized()
    with pytest.raises(FEOSPolicyError):
        ClipboardGateway(ws).prepare(EscalationPackage(id="pkg", case_id="case", context_package_id="ctx"), "x", PolicyResult(allowed=False))

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.adapters.clipboard_adapter import FakeClipboardAdapter
from _infra.feos.gateways import ClipboardGateway
from _infra.feos.storage import FEOSWorkspace


def test_clipboard_copy_and_receive(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos"); ws.ensure_initialized()
    export_dir = ws.case_dir("case_001") / "exports"
    export_dir.mkdir(parents=True)
    (export_dir / "clipboard.md").write_text("hello external", encoding="utf-8")
    fake = FakeClipboardAdapter()
    gateway = ClipboardGateway(ws, fake)
    session = gateway.dispatch_copy("case_001")
    assert fake.value == "hello external"
    assert session.human_actions[0].type == "copied_to_clipboard"
    fake.value = "## Root Cause\nSchema mismatch\n## Recommendations\n- Add field"
    response = gateway.receive_response("case_001")
    assert response.content_hash.startswith("sha256:")
    assert (ws.case_dir("case_001") / "responses" / f"{response.id}_raw.md").exists()

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 12:38:00

"""Export API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.app.main import create_app
from server.app.settings import Settings


def test_export_summary_api_generates_and_reads_markdown_with_audit() -> None:
    app = create_app(Settings(env="test"))

    with TestClient(app) as client:
        created = client.post(
            "/api/v1/exports/summary",
            json={
                "title": "Visit Summary",
                "events": [{"event_type": "feeding", "summary": "90ml"}],
                "format": "md",
                "generated_by": "u1",
            },
        )
        assert created.status_code == 200
        export_id = created.json()["id"]
        downloaded = client.get(f"/api/v1/exports/{export_id}")

    assert downloaded.status_code == 200
    assert downloaded.text.startswith("# Visit Summary")
    assert "feeding" in downloaded.text
    assert app.state.audit_sink.records[-1].action == "export.summary"


def test_export_summary_api_generates_pdf_placeholder() -> None:
    app = create_app(Settings(env="test"))

    with TestClient(app) as client:
        created = client.post(
            "/api/v1/exports/summary",
            json={"title": "PDF Summary", "events": [], "format": "pdf"},
        )
        export_id = created.json()["id"]
        downloaded = client.get(f"/api/v1/exports/{export_id}")

    assert created.status_code == 200
    assert downloaded.status_code == 200
    assert downloaded.content.startswith(b"PDF export placeholder")

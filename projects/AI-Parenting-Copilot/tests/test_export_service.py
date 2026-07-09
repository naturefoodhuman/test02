# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 08:40:00

"""APC-T043 export service tests."""

from __future__ import annotations

from pathlib import Path

from server.app.export.service import ExportService
from server.app.media.export.markdown import render_markdown_summary


def test_markdown_summary_redacts_to_authorized_fields() -> None:
    markdown = render_markdown_summary(
        title="7d Summary",
        events=[{"event_type": "feeding", "summary": "90ml"}],
    )

    assert "# 7d Summary" in markdown
    assert "feeding" in markdown
    assert "raw_input" not in markdown


def test_export_service_generates_md_and_pdf_placeholder(tmp_path: Path) -> None:
    service = ExportService(tmp_path)

    md = service.export_summary(
        title="Visit Summary",
        events=[{"event_type": "temperature", "summary": "37.2C"}],
        format="md",
        generated_by="u1",
    )
    pdf = service.export_summary(title="Visit Summary", events=[], format="pdf")

    assert Path(md.local_path).read_text(encoding="utf-8").startswith("# Visit Summary")
    assert Path(pdf.local_path).read_bytes().startswith(b"PDF export placeholder")
    assert md.generated_by == "u1"

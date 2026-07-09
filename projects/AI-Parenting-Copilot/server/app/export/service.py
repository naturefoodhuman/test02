# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 08:40:00


"""Export service for MD/PDF local files."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from server.app.common.clock import utc_now
from server.app.common.ids import new_ulid
from server.app.media.export.markdown import render_markdown_summary
from server.app.media.export.pdf import render_pdf_placeholder


class ExportRecord(BaseModel):
    id: str = Field(default_factory=new_ulid)
    format: str
    local_path: str
    generated_at: str = Field(default_factory=lambda: utc_now().isoformat())
    generated_by: str | None = None


class ExportService:
    def __init__(self, root: Path | str = "runtime/exports") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.records: dict[str, ExportRecord] = {}

    def export_summary(
        self,
        *,
        title: str,
        events: list[dict[str, object]],
        format: str = "md",
        generated_by: str | None = None,
    ) -> ExportRecord:
        markdown = render_markdown_summary(title=title, events=events)
        export_id = new_ulid()
        if format == "md":
            path = self.root / f"{export_id}.md"
            path.write_text(markdown, encoding="utf-8")
        elif format == "pdf":
            path = self.root / f"{export_id}.pdf"
            path.write_bytes(render_pdf_placeholder(markdown))
        else:
            raise ValueError("format must be md or pdf")
        record = ExportRecord(
            id=export_id,
            format=format,
            local_path=str(path),
            generated_by=generated_by,
        )
        self.records[record.id] = record
        return record

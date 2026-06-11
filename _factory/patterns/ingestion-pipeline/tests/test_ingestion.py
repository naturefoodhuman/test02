# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-11 22:10:00 CST
"""Ingestion 层测试（沙箱可跑通：验证调度、降级、统一输出）。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ingestion.models import SourceType, StructuredDoc  # noqa: E402
from ingestion.pipeline import ingest_dir, ingest_file, pick_processor, save_doc  # noqa: E402
from ingestion.processors import PdfProcessor, TextProcessor  # noqa: E402


def test_pick_processor_by_ext() -> None:
    assert isinstance(pick_processor(Path("a.txt")), TextProcessor)
    assert isinstance(pick_processor(Path("a.PDF")), PdfProcessor)  # 大小写不敏感
    assert pick_processor(Path("a.xyz")) is None


def test_text_processor_structured(tmp_path) -> None:
    f = tmp_path / "note.md"
    f.write_text("# 借款台账\n\n张三借款5万\n\n## 时间线\n2024年1月借出", encoding="utf-8")
    doc = ingest_file(f)
    assert doc.source_type == SourceType.TEXT
    assert doc.title == "借款台账"
    kinds = [s.kind for s in doc.segments]
    assert "heading" in kinds and "paragraph" in kinds
    # 标题层级被正确解析
    h = [s for s in doc.segments if s.kind == "heading"]
    assert h[0].meta["level"] == 1


def test_pdf_graceful_degrade(tmp_path, monkeypatch) -> None:
    # 强制模拟"无任何 PDF 库"场景，验证降级逻辑（不依赖沙箱是否装了 markitdown）
    import ingestion.processors as P

    monkeypatch.setattr(P, "_lib_available", lambda name: False)
    f = tmp_path / "contract.pdf"
    f.write_bytes(b"%PDF-1.4 fake")
    doc = ingest_file(f)
    assert doc.source_type == SourceType.PDF
    assert doc.meta.get("processor") == "none(降级)"
    assert doc.warnings  # 降级必有提示


def test_pdf_real_markitdown_when_available(tmp_path) -> None:
    # 若装了 markitdown，PDF/文本类应被真实解析（不再是空占位）
    import importlib.util

    if importlib.util.find_spec("markitdown") is None:
        import pytest

        pytest.skip("未装 markitdown，跳过真实解析验证")
    # 用一个 markitdown 必定支持的纯文本伪装（验证"真实调用并填充内容"路径）
    f = tmp_path / "doc.txt"
    f.write_text("# 标题\n正文内容", encoding="utf-8")
    # 直接验证 _run_markitdown 真实填充
    from ingestion.models import SourceType as ST
    from ingestion.models import StructuredDoc
    from ingestion.processors import _run_markitdown

    d = StructuredDoc(source_path=str(f), source_type=ST.TEXT)
    assert _run_markitdown(f, d) is True
    assert d.markdown and d.segments  # 真实有内容


def test_audio_degrade_mentions_funasr(tmp_path, monkeypatch) -> None:
    # 模拟无 funasr，验证降级提示
    import ingestion.processors as P

    monkeypatch.setattr(P, "_lib_available", lambda name: False)
    f = tmp_path / "call.wav"
    f.write_bytes(b"RIFFfake")
    doc = ingest_file(f)
    assert doc.source_type == SourceType.AUDIO
    assert any("FunASR" in w for w in doc.warnings)


def test_unknown_type(tmp_path) -> None:
    f = tmp_path / "x.xyz"
    f.write_text("?", encoding="utf-8")
    doc = ingest_file(f)
    assert doc.source_type == SourceType.UNKNOWN
    assert doc.warnings


def test_ingest_dir_and_save(tmp_path) -> None:
    (tmp_path / "a.txt").write_text("# A\n内容", encoding="utf-8")
    (tmp_path / "b.pdf").write_bytes(b"%PDF fake")
    docs = ingest_dir(tmp_path)
    assert len(docs) == 2
    out = tmp_path / "out"
    for d in docs:
        md, js = save_doc(d, out)
        assert md.exists() and js.exists()


def test_structured_doc_json_roundtrip() -> None:
    doc = StructuredDoc(source_path="x.txt", source_type=SourceType.TEXT, title="T", markdown="hi")
    s = doc.to_json()
    assert '"source_type": "text"' in s
    assert "hi" in s

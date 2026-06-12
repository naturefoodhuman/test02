# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建/修改时间（北京时间，精确到秒）：2026-06-11 23:40:00 CST
"""各类型处理器：把原始资料转为 StructuredDoc（真实调用，非占位）。

第13轮修复：上一版只"检测到库"但没真正调用 → 输出空内容。
本版改为：检测到库 → **真实调用解析** → 填充 markdown/segments；
调用失败或无库 → 降级并记录真实错误/提示。

优先级：
- PDF：MinerU > MarkItDown > pypdf > 占位
- 图片：MinerU > (OCR) > 占位
- 音频：FunASR(转写+说话人分离) > 占位
- Office：MarkItDown > 占位
零核心依赖：缺库自动降级，不影响整体流程。
"""
from __future__ import annotations

import abc
import importlib.util
from pathlib import Path

from ingestion.models import Segment, SourceType, StructuredDoc


def _lib_available(name: str) -> bool:
    """检测某个第三方库是否可导入（不真正 import，避免副作用）。"""
    return importlib.util.find_spec(name) is not None


def _segments_from_markdown(md: str) -> list[Segment]:
    """把 Markdown 文本切成 heading/paragraph 片段（通用切分）。"""
    segs: list[Segment] = []
    for block in md.split("\n"):
        s = block.strip()
        if not s:
            continue
        if s.startswith("#"):
            level = len(s) - len(s.lstrip("#"))
            segs.append(Segment(kind="heading", text=s.lstrip("# ").strip(), meta={"level": level}))
        elif s.startswith("|") and s.endswith("|"):
            segs.append(Segment(kind="table", text=s))
        else:
            segs.append(Segment(kind="paragraph", text=s))
    return segs


def _run_markitdown(path: Path, doc: StructuredDoc) -> bool:
    """用 MarkItDown 真实解析；成功填充 doc 并返回 True。"""
    try:
        from markitdown import MarkItDown  # type: ignore

        md = MarkItDown()
        result = md.convert(str(path))
        text = (getattr(result, "markdown", None) or getattr(result, "text_content", "") or "").strip()
        doc.markdown = text
        doc.segments = _segments_from_markdown(text)
        if getattr(result, "title", None):
            doc.title = result.title
        doc.meta["processor"] = "MarkItDown"
        if not text:
            doc.warnings.append("MarkItDown 返回空内容（文件可能是扫描件/无文本层，建议改用 MinerU）")
        return True
    except Exception as e:  # noqa: BLE001
        doc.warnings.append(f"MarkItDown 调用失败: {e}")
        return False


def _run_mineru(path: Path, doc: StructuredDoc) -> bool:
    """用 MinerU 真实解析（PDF/图片，中文复杂版面/扫描件首选）。

    MinerU 3.x：优先调 SDK `do_parse`，失败回退调 CLI `mineru -p -o`，
    两者都把生成的 .md 读回填充 doc。再不行才降级提示。
    """
    import subprocess
    import tempfile

    out_dir = Path(tempfile.mkdtemp(prefix="mineru_"))

    def _read_back(base: Path) -> str:
        """从 MinerU 输出目录读回生成的 markdown。"""
        mds = sorted(base.rglob("*.md"))
        for m in mds:
            txt = m.read_text(encoding="utf-8", errors="replace").strip()
            if txt:
                return txt
        return ""

    # ① 优先 SDK（MinerU 3.x: mineru.cli.common.do_parse）
    try:
        from mineru.cli.common import do_parse, read_fn  # type: ignore

        pdf_bytes = read_fn(path)
        do_parse(
            output_dir=str(out_dir),
            pdf_file_names=[path.stem],
            pdf_bytes_list=[pdf_bytes],
            p_lang_list=["ch"],
            backend="pipeline",
            parse_method="auto",
        )
        md = _read_back(out_dir)
        if md:
            doc.markdown = md
            doc.segments = _segments_from_markdown(md)
            doc.meta["processor"] = "MinerU(SDK)"
            return True
    except Exception as e:  # noqa: BLE001
        doc.warnings.append(f"MinerU SDK 调用未成功（{e}），尝试 CLI…")

    # ② 回退 CLI（你已验证 mineru 3.2.3 CLI 可用）
    try:
        import shutil

        if shutil.which("mineru"):
            subprocess.run(
                ["mineru", "-p", str(path), "-o", str(out_dir), "--source", "local"],
                check=True, capture_output=True, timeout=1800,
            )
            md = _read_back(out_dir)
            if md:
                doc.markdown = md
                doc.segments = _segments_from_markdown(md)
                doc.meta["processor"] = "MinerU(CLI)"
                return True
            doc.warnings.append("MinerU CLI 运行了但未读到 markdown 输出。")
        else:
            doc.warnings.append("未找到 mineru 命令（确认在装了 mineru 的环境里运行）。")
    except Exception as e:  # noqa: BLE001
        doc.warnings.append(f"MinerU CLI 调用失败: {e}")
    return False


def _run_funasr(path: Path, doc: StructuredDoc) -> bool:
    """用 FunASR 真实转写 + 说话人分离；成功填充 utterance segments。"""
    try:
        from funasr import AutoModel  # type: ignore

        # Paraformer-zh + VAD + 标点 + 说话人分离（cam++）——中文通话录音标准组合
        model = AutoModel(
            model="paraformer-zh",
            vad_model="fsmn-vad",
            punc_model="ct-punc",
            spk_model="cam++",
            disable_update=True,
        )
        res = model.generate(input=str(path), batch_size_s=300)
        doc.meta["processor"] = "FunASR(paraformer-zh+spk)"
        # FunASR 返回结构：res[0]['sentence_info'] 含 spk/start/end/text（带说话人分离时）
        item = res[0] if res else {}
        sent_info = item.get("sentence_info") if isinstance(item, dict) else None
        md_lines: list[str] = [f"# 录音转写：{path.stem}", ""]
        if sent_info:
            for s in sent_info:
                spk = s.get("spk", "?")
                text = s.get("text", "").strip()
                start = s.get("start", 0)
                if not text:
                    continue
                doc.segments.append(
                    Segment(kind="utterance", text=text, meta={"speaker": f"说话人{spk}", "start_ms": start})
                )
                md_lines.append(f"- **说话人{spk}**（{start}ms）：{text}")
        else:
            # 无说话人信息时退化为整段文本
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            doc.segments.append(Segment(kind="utterance", text=text))
            md_lines.append(text)
        doc.markdown = "\n".join(md_lines)
        return True
    except Exception as e:  # noqa: BLE001
        doc.warnings.append(f"FunASR 调用失败: {e}（确认已 pip install funasr 且首次会下载模型）")
        return False


class BaseProcessor(abc.ABC):
    """处理器抽象基类（专家接口）。"""

    extensions: tuple[str, ...] = ()
    source_type: SourceType = SourceType.UNKNOWN

    @abc.abstractmethod
    def process(self, path: Path) -> StructuredDoc:
        raise NotImplementedError


class TextProcessor(BaseProcessor):
    """纯文本 / Markdown：直接读入，按行切段。零依赖。"""

    extensions = (".txt", ".md", ".markdown")
    source_type = SourceType.TEXT

    def process(self, path: Path) -> StructuredDoc:
        text = path.read_text(encoding="utf-8", errors="replace")
        segs = _segments_from_markdown(text)
        title = segs[0].text if segs and segs[0].kind == "heading" else path.stem
        return StructuredDoc(
            source_path=str(path), source_type=self.source_type, title=title,
            markdown=text, segments=segs, meta={"processor": "TextProcessor"},
        )


class PdfProcessor(BaseProcessor):
    """PDF：MinerU > MarkItDown > pypdf > 占位。真实调用。"""

    extensions = (".pdf",)
    source_type = SourceType.PDF

    def process(self, path: Path) -> StructuredDoc:
        doc = StructuredDoc(source_path=str(path), source_type=self.source_type, title=path.stem)
        # 1) MinerU（中文复杂版面/扫描件最佳）
        if _lib_available("mineru") or _lib_available("magic_pdf"):
            if _run_mineru(path, doc):
                return doc
            # MinerU 未成功 → 继续尝试 MarkItDown
        # 2) MarkItDown（有文本层的 PDF 效果好）
        if _lib_available("markitdown"):
            if _run_markitdown(path, doc):
                return doc
        # 3) pypdf 纯文本降级
        if _lib_available("pypdf"):
            try:
                import pypdf  # type: ignore

                reader = pypdf.PdfReader(str(path))
                text = "\n\n".join((p.extract_text() or "") for p in reader.pages).strip()
                doc.markdown = text
                doc.segments = [Segment(kind="paragraph", text=t.strip())
                                for t in text.split("\n\n") if t.strip()]
                doc.meta["processor"] = "pypdf(降级:纯文本)"
                if not text:
                    doc.warnings.append("pypdf 未提取到文本（可能是扫描件），建议安装 MinerU 做 OCR。")
                return doc
            except Exception as e:  # noqa: BLE001
                doc.warnings.append(f"pypdf 解析失败: {e}")
        doc.meta["processor"] = "none(降级)"
        doc.warnings.append("未安装可用 PDF 解析库。真机请安装 MinerU 或 markitdown。")
        return doc


class ImageProcessor(BaseProcessor):
    """图片：MinerU/OCR 真实调用 > 占位。"""

    extensions = (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff")
    source_type = SourceType.IMAGE

    def process(self, path: Path) -> StructuredDoc:
        doc = StructuredDoc(source_path=str(path), source_type=self.source_type, title=path.stem)
        # MarkItDown 也能处理图片（走其 OCR/Caption 路径，需相应依赖）
        if _lib_available("mineru") or _lib_available("magic_pdf"):
            if _run_mineru(path, doc):
                return doc
        if _lib_available("markitdown"):
            if _run_markitdown(path, doc):
                # markitdown 对图片可能仅返回元数据；若空则提示装 MinerU
                if not doc.markdown:
                    doc.warnings.append("图片未识别出文字。中文图片(如检验报告/借据)强烈建议安装 MinerU 做 OCR。")
                return doc
        doc.meta["processor"] = "none(降级)"
        doc.warnings.append("未安装 OCR/MinerU。真机请安装 MinerU 以识别图片文字。")
        return doc


class AudioProcessor(BaseProcessor):
    """通话录音：FunASR(转写+说话人分离) 真实调用 > 占位。"""

    extensions = (".wav", ".mp3", ".m4a", ".flac", ".aac")
    source_type = SourceType.AUDIO

    def process(self, path: Path) -> StructuredDoc:
        doc = StructuredDoc(source_path=str(path), source_type=self.source_type, title=path.stem)
        if _lib_available("funasr"):
            if _run_funasr(path, doc):
                return doc
            # FunASR 在但调用失败 → 已记 warning
        else:
            doc.warnings.append("未安装 FunASR。真机请安装：pip install funasr（中文最强、本地、说话人分离）。")
        doc.meta.setdefault("processor", "none(降级)")
        return doc


class OfficeProcessor(BaseProcessor):
    """Office：MarkItDown 真实调用 > 占位。"""

    extensions = (".docx", ".pptx", ".xlsx", ".doc", ".ppt", ".xls")
    source_type = SourceType.OFFICE

    def process(self, path: Path) -> StructuredDoc:
        doc = StructuredDoc(source_path=str(path), source_type=self.source_type, title=path.stem)
        if _lib_available("markitdown"):
            if _run_markitdown(path, doc):
                return doc
            # markitdown 在但调用失败（多半缺子依赖）→ 已记真实错误，给精确建议
            doc.meta["processor"] = "none(降级)"
            doc.warnings.append("建议安装全格式支持：pip install 'markitdown[all]'（含 docx/pptx/xlsx）。")
            return doc
        doc.meta["processor"] = "none(降级)"
        doc.warnings.append("未安装 markitdown。真机请安装：pip install 'markitdown[all]'（MIT，多格式）。")
        return doc


#: 全部内置处理器（调度器按后缀匹配）
ALL_PROCESSORS: tuple[BaseProcessor, ...] = (
    TextProcessor(),
    PdfProcessor(),
    ImageProcessor(),
    AudioProcessor(),
    OfficeProcessor(),
)

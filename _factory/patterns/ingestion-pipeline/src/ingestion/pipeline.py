# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-11 22:10:00 CST
"""Ingestion 调度器：按文件类型路由到处理器，批量产出结构化结果。

工厂通用能力入口：项目只管"把一堆资料丢进来"，调度器负责选处理器、
统一输出 StructuredDoc（Markdown + JSON），并落盘供下游 RAG/分析使用。
"""
from __future__ import annotations

import logging
from pathlib import Path

from ingestion.models import SourceType, StructuredDoc
from ingestion.processors import ALL_PROCESSORS, BaseProcessor

logger = logging.getLogger("forge.ingestion")

# 后缀 → 处理器 映射（启动时构建一次）
_EXT_MAP: dict[str, BaseProcessor] = {}
for _p in ALL_PROCESSORS:
    for _ext in _p.extensions:
        _EXT_MAP[_ext] = _p


def pick_processor(path: Path) -> BaseProcessor | None:
    """根据文件后缀选处理器；不支持则返回 None。"""
    return _EXT_MAP.get(path.suffix.lower())


def ingest_file(path: str | Path) -> StructuredDoc:
    """处理单个文件 → StructuredDoc。

    Args:
        path: 文件路径。

    Returns:
        StructuredDoc；不支持的类型返回带 warning 的 UNKNOWN 文档。
    """
    p = Path(path)
    proc = pick_processor(p)
    if proc is None:
        doc = StructuredDoc(source_path=str(p), source_type=SourceType.UNKNOWN, title=p.stem)
        doc.warnings.append(f"不支持的文件类型: {p.suffix}（可在 processors.py 扩展处理器）")
        return doc
    logger.info("ingest %s via %s", p.name, type(proc).__name__)
    return proc.process(p)


def ingest_dir(root: str | Path, *, recursive: bool = True) -> list[StructuredDoc]:
    """批量处理目录下所有文件。

    Args:
        root: 资料目录。
        recursive: 是否递归子目录。

    Returns:
        StructuredDoc 列表（每个文件一个）。
    """
    base = Path(root)
    if not base.exists():
        raise FileNotFoundError(f"目录不存在: {base}")
    it = base.rglob("*") if recursive else base.glob("*")
    docs: list[StructuredDoc] = []
    for f in sorted(it):
        if not f.is_file():
            continue
        # 跳过隐藏文件/系统垃圾（macOS .DS_Store、Office 临时 ~$ 文件等）
        if f.name.startswith(".") or f.name.startswith("~$"):
            continue
        docs.append(ingest_file(f))
    return docs


def save_doc(doc: StructuredDoc, out_dir: str | Path) -> tuple[Path, Path]:
    """把一个 StructuredDoc 落盘为 .md 和 .json 两份。

    Returns:
        (md 路径, json 路径)
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = Path(doc.source_path).stem
    md_path = out / f"{stem}.md"
    json_path = out / f"{stem}.json"
    md_path.write_text(doc.markdown or f"# {doc.title}\n\n(无文本内容/待真机处理器解析)\n", encoding="utf-8")
    json_path.write_text(doc.to_json(), encoding="utf-8")
    return md_path, json_path

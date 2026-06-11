# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-11 22:10:00 CST
"""Ingestion 层统一数据模型。

设计理由：不管输入是 PDF / 图片 / 录音 / Office，最终都归一到同一个
StructuredDoc 结构，供下游 RAG / 分析 / 台账统一消费（满足老板要点6：
不同格式统一转为结构化格式）。这样下游代码不关心来源格式。
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any
import json


class SourceType(str, Enum):
    """输入资料的类型。"""

    PDF = "pdf"
    IMAGE = "image"
    AUDIO = "audio"
    OFFICE = "office"      # docx/pptx/xlsx
    TEXT = "text"          # txt/md
    HTML = "html"
    UNKNOWN = "unknown"


@dataclass
class Segment:
    """结构化片段（一个标题/段落/表格/一句话转写等）。"""

    kind: str                      # heading / paragraph / table / utterance / image_caption ...
    text: str
    meta: dict[str, Any] = field(default_factory=dict)  # 如 {speaker, start_ms, level, page}


@dataclass
class StructuredDoc:
    """统一结构化文档（所有处理器的最终产出）。"""

    source_path: str
    source_type: SourceType
    title: str = ""
    markdown: str = ""             # 结构化 Markdown（人读 + RAG 切分）
    segments: list[Segment] = field(default_factory=list)  # 机器可读片段
    meta: dict[str, Any] = field(default_factory=dict)     # 处理器、耗时、是否降级等
    warnings: list[str] = field(default_factory=list)      # 降级/质量提示

    def to_dict(self) -> dict[str, Any]:
        """转为可 JSON 序列化的字典。"""
        d = asdict(self)
        d["source_type"] = self.source_type.value
        return d

    def to_json(self, *, ensure_ascii: bool = False, indent: int = 2) -> str:
        """转为 JSON 字符串（默认保留中文）。"""
        return json.dumps(self.to_dict(), ensure_ascii=ensure_ascii, indent=indent)

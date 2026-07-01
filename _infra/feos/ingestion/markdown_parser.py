# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from .format_detector import detect_format
from .section_extractor import extract_sections
from .yaml_block_parser import extract_yaml_blocks


def parse_markdown_sections(text: str) -> dict:
    if not text.strip():
        return {"format": "empty", "sections": {}, "yaml_blocks": [], "warnings": ["empty response"]}
    blocks, warnings = extract_yaml_blocks(text)
    return {"format": detect_format(text), "sections": extract_sections(text), "yaml_blocks": blocks, "warnings": warnings}

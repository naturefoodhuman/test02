# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.ingestion.markdown_parser import parse_markdown_sections
from _infra.feos.ingestion.yaml_block_parser import extract_yaml_blocks


def test_markdown_and_yaml_parsers():
    text = "## Root Cause\nSchema mismatch\n```yaml\nrecommendations:\n - Add tests\n```"
    parsed = parse_markdown_sections(text)
    assert parsed["format"] == "markdown_with_yaml"
    assert "root_cause" in parsed["sections"]
    blocks, warnings = extract_yaml_blocks(text)
    assert blocks[0]["recommendations"] == ["Add tests"]
    assert warnings == []


def test_malformed_yaml_warning_and_empty_response():
    parsed = parse_markdown_sections("```yaml\na: [\n```")
    assert parsed["warnings"]
    empty = parse_markdown_sections("")
    assert empty["format"] == "empty"

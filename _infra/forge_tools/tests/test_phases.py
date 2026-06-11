# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
"""五阶段状态机测试。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forge.phases import PHASES, can_advance, next_phase  # noqa: E402


def test_phase_order() -> None:
    assert PHASES == ("DISCOVERY", "SPEC", "BUILD", "HARDEN", "RETRO")


def test_next_phase() -> None:
    assert next_phase("DISCOVERY") == "SPEC"
    assert next_phase("HARDEN") == "RETRO"
    assert next_phase("RETRO") is None


def test_next_phase_invalid() -> None:
    with pytest.raises(ValueError):
        next_phase("NOPE")


def test_can_advance_blocks_without_artifacts() -> None:
    ok, missing = can_advance("DISCOVERY", set())
    assert not ok
    assert "docs/DISCOVERY.md" in missing


def test_can_advance_passes_with_artifacts() -> None:
    ok, missing = can_advance("DISCOVERY", {"docs/DISCOVERY.md"})
    assert ok and missing == []


def test_spec_needs_multiple_artifacts() -> None:
    ok, missing = can_advance("SPEC", {"docs/SPEC.md"})
    assert not ok
    assert "docs/TASK_GRAPH.md" in missing
    assert "docs/RISK.md" in missing

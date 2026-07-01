# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.evidence.importance import importance_for_type
from _infra.feos.evidence.normalizer import EvidenceNormalizer
from _infra.feos.evidence.parsers.diff_parser import parse_diff_paths
from _infra.feos.evidence.parsers.log_excerpt import compact_log_excerpt
from _infra.feos.ports.collectors import CollectedEvidence


def test_importance_defaults():
    assert importance_for_type("stack_trace") == 0.95
    assert importance_for_type("git_diff") == 0.90
    assert importance_for_type("unknown") == 0.30


def test_stacktrace_normalizer_and_preview():
    item = CollectedEvidence(collector_id="stack", evidence_type="stack_trace", raw_content='Traceback\n  File "x.py"\nValueError: bad')
    preview, normalized = EvidenceNormalizer().normalize(item)
    assert "ValueError" in preview
    assert normalized["frame_count"] == 1


def test_diff_parser_and_log_excerpt():
    assert parse_diff_paths("--- a/x.py\n+++ b/x.py\n@@") == ["x.py"]
    assert compact_log_excerpt("a\na\nb", max_lines=10).splitlines() == ["a", "b"]

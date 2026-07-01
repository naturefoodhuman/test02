# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Evidence normalization."""

from __future__ import annotations

from _infra.feos.models.enums import EvidenceType
from _infra.feos.ports.collectors import CollectedEvidence

from .parsers.diff_parser import parse_diff_paths
from .parsers.log_excerpt import compact_log_excerpt
from .parsers.stacktrace_parser import parse_stacktrace


class EvidenceNormalizer:
    def __init__(self, preview_chars: int = 500):
        self.preview_chars = preview_chars

    def normalize(self, collected: CollectedEvidence) -> tuple[str, dict]:
        text = collected.raw_content or ""
        normalized = {}
        try:
            if collected.evidence_type == EvidenceType.STACK_TRACE:
                normalized = parse_stacktrace(text)
            elif collected.evidence_type == EvidenceType.GIT_DIFF:
                normalized = {"paths": parse_diff_paths(text)}
            elif collected.evidence_type == EvidenceType.LOG:
                text = compact_log_excerpt(text)
                normalized = {"line_count": len(text.splitlines())}
            else:
                normalized = {"length": len(text)}
        except Exception as exc:
            normalized = {"normalization_error": str(exc)}
        return text[: self.preview_chars], normalized

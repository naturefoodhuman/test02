# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.evidence.collectors import LogCollector, RuntimeCollector, StackTraceCollector, TestCollector
from _infra.feos.ports.collectors import EvidenceCollectionRequest


def test_stack_runtime_test_and_log_collectors(tmp_path):
    log = tmp_path / "run.log"
    log.write_text("err\nerr\nwarn", encoding="utf-8")
    req = EvidenceCollectionRequest(case_id="case_001", logs=["run.log"], commands=["pytest"], task_metadata={"stack_trace": "Traceback\nValueError", "test_output": "FAILED"})
    assert StackTraceCollector().collect(req)[0].evidence_type == "stack_trace"
    assert TestCollector().collect(req)[0].evidence_type == "failing_test"
    assert RuntimeCollector().collect(req)[0].evidence_type == "runtime_env"
    assert LogCollector(tmp_path).collect(req)[0].evidence_type == "log"

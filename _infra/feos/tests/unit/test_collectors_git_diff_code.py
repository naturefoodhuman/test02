# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.evidence.collectors import CodeCollector, DiffCollector, GitCollector
from _infra.feos.ports.collectors import EvidenceCollectionRequest


class FakeGitAdapter:
    def current_branch(self): return "main"
    def current_commit(self): return "abc"
    def status(self): return " M file.py"
    def diff(self, paths=None): return "diff --git a/file.py b/file.py\n+++ b/file.py\n@@"


def test_git_and_diff_collectors_with_fake_adapter(tmp_path):
    req = EvidenceCollectionRequest(case_id="case_001")
    git_ev = GitCollector(tmp_path, FakeGitAdapter()).collect(req)[0]
    diff_ev = DiffCollector(tmp_path, FakeGitAdapter()).collect(req)[0]
    assert "branch: main" in git_ev.raw_content
    assert diff_ev.evidence_type == "git_diff"


def test_code_collector_reads_allowed_and_skips_env(tmp_path):
    (tmp_path / "a.py").write_text("print('ok')", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=x", encoding="utf-8")
    req = EvidenceCollectionRequest(case_id="case_001", paths=["a.py", ".env"])
    evs = CodeCollector(tmp_path).collect(req)
    assert len(evs) == 1
    assert "print" in evs[0].raw_content

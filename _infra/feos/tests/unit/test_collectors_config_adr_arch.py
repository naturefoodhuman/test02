# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.evidence import create_default_registry
from _infra.feos.evidence.collectors import ADRCollector, ArchitectureCollector, ConfigCollector, DependencyCollector, EnvironmentCollector
from _infra.feos.ports.collectors import EvidenceCollectionRequest


def test_config_dependency_adr_arch_collectors(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "x.yaml").write_text("a: 1", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=1", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("pytest", encoding="utf-8")
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    (tmp_path / "docs" / "adr" / "ADR-001.md").write_text("# ADR", encoding="utf-8")
    (tmp_path / "FEOS_ARCHITECTURE_FINAL.md").write_text("# Arch", encoding="utf-8")
    req = EvidenceCollectionRequest(case_id="case_001")
    assert ConfigCollector(tmp_path).collect(req)[0].evidence_type == "config"
    assert DependencyCollector(tmp_path).collect(req)[0].evidence_type == "dependency_lock"
    assert ADRCollector(tmp_path).collect(req)[0].origin == "adr"
    assert ArchitectureCollector(tmp_path).collect(req)[0].origin == "architecture_doc"
    assert EnvironmentCollector().collect(req)[0].evidence_type == "runtime_env"
    registry = create_default_registry(tmp_path)
    assert registry.get("user_input").collector_id == "user_input"

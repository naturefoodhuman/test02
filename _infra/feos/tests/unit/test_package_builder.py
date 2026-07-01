# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ContextPackage, Evidence, EvidenceContent, EvidenceSecurity, EvidenceSource
from _infra.feos.package import EscalationPackageBuilder, EscalationPackageService
from _infra.feos.repositories import PackageRepository
from _infra.feos.storage import FEOSWorkspace, read_json


def test_package_builder_manifest_and_attachment_filter(tmp_path):
    ctx = ContextPackage(id="ctx_001", case_id="case_001")
    ev = Evidence(id="ev1", case_id="case_001", source=EvidenceSource(collector="c", origin="o"), content=EvidenceContent(raw_ref="secret.txt"), security=EvidenceSecurity(contains_secret=True))
    pkg, manifest = EscalationPackageBuilder().build(ctx, evidence=[ev])
    assert pkg.gateway == "clipboard"
    assert manifest["output_contract"]["external_execution_allowed"] is False
    assert manifest["attachments"] == []


def test_package_service_saves_files(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos"); ws.ensure_initialized()
    ctx = ContextPackage(id="ctx_001", case_id="case_001")
    pkg = EscalationPackageService(PackageRepository(ws)).build_and_save(ctx)
    assert read_json(ws.root / "cases" / "case_001" / "package" / "package.json")["id"] == pkg.id
    assert read_json(ws.root / "cases" / "case_001" / "package" / "manifest.json")["package_id"] == pkg.id

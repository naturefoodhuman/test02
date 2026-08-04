# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-05 01:25:00

"""External validation bundle tests."""

from __future__ import annotations

import json
from pathlib import Path

from server.app.ops.external_validation_bundle import build_external_validation_bundle


def test_external_validation_bundle_writes_all_templates(tmp_path: Path) -> None:
    bundle = build_external_validation_bundle(output_dir=tmp_path)

    assert Path(bundle.plan_json).exists()
    assert Path(bundle.plan_markdown).exists()
    assert Path(bundle.closeout_recommendation_json).exists()
    assert Path(bundle.closeout_recommendation_markdown).exists()
    assert len(bundle.evidence_templates) >= 10
    assert len(bundle.signoff_templates) == 4
    assert all(Path(path).exists() for path in bundle.evidence_templates)
    assert all(Path(path).exists() for path in bundle.signoff_templates)
    assert any(
        "APC-T044" in Path(path).read_text(encoding="utf-8")
        for path in bundle.evidence_templates
    )


def test_external_validation_bundle_manifest_is_json(tmp_path: Path) -> None:
    bundle = build_external_validation_bundle(output_dir=tmp_path)
    manifest = json.loads((tmp_path / "external-validation-bundle.json").read_text())

    assert manifest["output_dir"] == str(tmp_path)
    assert manifest["plan_json"] == bundle.plan_json
    assert "make apc-closeout-gate" in " ".join(manifest["notes"])

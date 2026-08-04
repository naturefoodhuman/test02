# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 23:20:00

"""External validation evidence verifier tests."""

from __future__ import annotations

from pathlib import Path

from server.app.ops.external_evidence import (
    ExternalValidationEvidence,
    build_evidence_template,
    validate_external_evidence,
    write_evidence_template,
)


def test_external_evidence_template_contains_required_keys() -> None:
    template = build_evidence_template("APC-T044")

    assert template.task_id == "APC-T044"
    assert template.status == "pending"
    assert "pg_dump_file_and_nas_path" in template.evidence
    assert "disposable_db_restore_log_and_db_current_output" in template.evidence


def test_external_evidence_validator_accepts_complete_passed_evidence() -> None:
    template = build_evidence_template("APC-T040")
    evidence = ExternalValidationEvidence(
        task_id=template.task_id,
        status="passed",
        operator="operator-1",
        completed_at="2026-08-04T23:20:00+08:00",
        evidence={key: f"artifact://{key}" for key in template.evidence},
    )

    result = validate_external_evidence(evidence)

    assert result.ok is True
    assert result.errors == ()
    assert (
        "mqtt_broker_logs_showing_telemetry_from_physical_device"
        in result.required_evidence_keys
    )


def test_external_evidence_validator_rejects_missing_fields() -> None:
    result = validate_external_evidence(build_evidence_template("APC-T038"))

    assert result.ok is False
    assert "status must be passed" in result.errors
    assert any(error.startswith("missing evidence") for error in result.errors)


def test_external_evidence_template_can_be_written(tmp_path: Path) -> None:
    path = write_evidence_template("APC-T059", output_dir=tmp_path)

    assert path.exists()
    assert "APC-T059" in path.read_text(encoding="utf-8")

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 23:20:00

"""External validation evidence templates and verifier.

The remaining APC blockers require human/real-device/NAS/soak evidence. This module
turns the external validation plan into machine-checkable evidence artifacts so the
operator can submit consistent JSON after each local validation run.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from server.app.ops.external_validation import (
    ExternalValidationItem,
    build_external_validation_plan,
)


@dataclass(frozen=True, slots=True)
class ExternalValidationEvidence:
    task_id: str
    status: str
    operator: str
    completed_at: str
    evidence: dict[str, str] = field(default_factory=dict)
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExternalValidationEvidence:
        return cls(
            task_id=str(data.get("task_id", "")),
            status=str(data.get("status", "")),
            operator=str(data.get("operator", "")),
            completed_at=str(data.get("completed_at", "")),
            evidence={str(k): str(v) for k, v in dict(data.get("evidence", {})).items()},
            notes=str(data.get("notes")) if data.get("notes") is not None else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass(frozen=True, slots=True)
class ExternalEvidenceValidationResult:
    ok: bool
    task_id: str
    status: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    required_evidence_keys: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def build_evidence_template(task_id: str) -> ExternalValidationEvidence:
    item = _item_for(task_id)
    evidence = {_slug(value): "" for value in item.evidence_required}
    return ExternalValidationEvidence(
        task_id=item.task_id,
        status="pending",
        operator="",
        completed_at="",
        evidence=evidence,
        notes=f"Fill evidence for {item.title}; set status=passed when local validation succeeds.",
    )


def validate_external_evidence(
    evidence: ExternalValidationEvidence,
) -> ExternalEvidenceValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        item = _item_for(evidence.task_id)
    except ValueError as exc:
        return ExternalEvidenceValidationResult(
            ok=False,
            task_id=evidence.task_id,
            status=evidence.status,
            errors=(str(exc),),
        )
    required_keys = tuple(_slug(value) for value in item.evidence_required)
    if evidence.status != "passed":
        errors.append("status must be passed")
    if not evidence.operator:
        errors.append("operator is required")
    if not evidence.completed_at:
        errors.append("completed_at is required")
    for key in required_keys:
        if not evidence.evidence.get(key):
            errors.append(f"missing evidence: {key}")
    if item.resource_type in {"human_medical_review", "long_running_soak"}:
        warnings.append("manual review of attached evidence is still required")
    return ExternalEvidenceValidationResult(
        ok=not errors,
        task_id=evidence.task_id,
        status=evidence.status,
        errors=tuple(errors),
        warnings=tuple(warnings),
        required_evidence_keys=required_keys,
    )


def load_evidence_file(path: Path | str) -> ExternalValidationEvidence:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("external evidence file must contain a JSON object")
    return ExternalValidationEvidence.from_dict(data)


def write_evidence_template(
    task_id: str,
    *,
    output_dir: Path | str = "runtime/reports/external-evidence",
) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    template = build_evidence_template(task_id)
    path = output / f"{task_id.lower()}-evidence-template.json"
    path.write_text(template.to_json(), encoding="utf-8")
    return path


def _item_for(task_id: str) -> ExternalValidationItem:
    for item in build_external_validation_plan().items:
        if item.task_id == task_id:
            return item
    raise ValueError(f"external validation task not found: {task_id}")


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug[:80]

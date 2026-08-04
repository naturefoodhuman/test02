# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 22:10:00

"""External validation plan for remaining local-only blockers.

The project can automate code contracts, dry-runs, and fake-device E2E substitutes.
This module packages the remaining human-review/hardware/NAS/soak validation work
into a machine-readable checklist so the local Mac/device operator can execute it
without ambiguity.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ExternalValidationItem:
    task_id: str
    title: str
    resource_type: str
    blocked_by: str
    commands: tuple[str, ...]
    evidence_required: tuple[str, ...]
    success_criteria: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExternalValidationPlan:
    status: str
    items: tuple[ExternalValidationItem, ...]
    summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = [
            "# AI Parenting Copilot External Validation Plan",
            "",
            f"- Status: `{self.status}`",
            f"- Items: `{len(self.items)}`",
            "",
            "This plan lists validations that require human review, real devices, "
            "local credentials, NAS storage, or long-running soak. Automated reports "
            "must not be treated as substitutes for these external checks.",
            "",
        ]
        for item in self.items:
            lines.extend(
                [
                    f"## {item.task_id} — {item.title}",
                    "",
                    f"- Resource type: `{item.resource_type}`",
                    f"- Blocked by: {item.blocked_by}",
                    "- Commands:",
                    *[f"  - `{command}`" for command in item.commands],
                    "- Evidence required:",
                    *[f"  - {evidence}" for evidence in item.evidence_required],
                    "- Success criteria:",
                    *[f"  - {criterion}" for criterion in item.success_criteria],
                    "",
                ]
            )
        return "\n".join(lines)


def build_external_validation_plan() -> ExternalValidationPlan:
    items = tuple(_items())
    summary: dict[str, int] = {}
    for item in items:
        summary[item.resource_type] = summary.get(item.resource_type, 0) + 1
    return ExternalValidationPlan(
        status="waiting_for_external_validation",
        items=items,
        summary=summary,
    )


def write_external_validation_plan(
    plan: ExternalValidationPlan,
    *,
    output_dir: Path | str = "runtime/reports",
) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "external-validation-plan.json"
    md_path = output / "external-validation-plan.md"
    json_path.write_text(plan.to_json(), encoding="utf-8")
    md_path.write_text(plan.to_markdown(), encoding="utf-8")
    return json_path, md_path


def _items() -> list[ExternalValidationItem]:
    return [
        ExternalValidationItem(
            task_id="APC-T022",
            title="Vaccine production rule review",
            resource_type="human_medical_review",
            blocked_by="Official CN immunization schedule review and sign-off.",
            commands=("make rule-review-packet",),
            evidence_required=(
                "Generated rule review packet JSON/Markdown.",
                "Reviewer-approved mapping against official CN schedule.",
                "Signed decision on version to activate for production.",
            ),
            success_criteria=(
                "Reviewer confirms every vaccine due date/status rule.",
                "No production blocker remains in rule review packet for vaccine.",
            ),
        ),
        ExternalValidationItem(
            task_id="APC-T023",
            title="Growth full WHO table review",
            resource_type="human_medical_review",
            blocked_by="Full WHO LMS data import/review is not available in repo.",
            commands=("make rule-review-packet",),
            evidence_required=(
                "WHO table source and checksum.",
                "Golden cases covering imported LMS rows.",
                "Reviewer sign-off for growth interpretation copy.",
            ),
            success_criteria=(
                "Full table replaces simplified fixture for production profile.",
                "Reviewer confirms no single-point strong alert is emitted.",
            ),
        ),
        ExternalValidationItem(
            task_id="APC-T038",
            title="Camera RTSP/ISAPI device validation",
            resource_type="camera_device",
            blocked_by=(
                "Requires real camera endpoint, credentials, LAN access, "
                "and cloud-disabled check."
            ),
            commands=(
                "make deployment-readiness",
                "python3 -m pytest tests/test_camera_adapters.py -q",
                "curl http://127.0.0.1:8000/api/v1/cameras/nursery/snapshot "
                "--output /tmp/nursery.png",
            ),
            evidence_required=(
                "Snapshot image from local camera path.",
                "ISAPI health response status.",
                "Screenshot/proof camera vendor cloud is disabled.",
            ),
            success_criteria=(
                "Snapshot can be fetched on LAN without vendor cloud.",
                "Camera health is online and logs contain no credential leak.",
            ),
        ),
        ExternalValidationItem(
            task_id="APC-T039",
            title="Camera/Fregata/VLM shadow validation",
            resource_type="camera_vlm_device",
            blocked_by=(
                "Requires real Fregata/VLM endpoint, camera media, "
                "and shadow observation window."
            ),
            commands=(
                "make shadow-test",
                "make p0-readiness",
                "curl -X POST http://127.0.0.1:8000/api/v1/camera-shadow/evaluate",
            ),
            evidence_required=(
                "Shadow report with false-positive review.",
                "Fregata/VLM dry-run or dispatch response logs.",
                "CameraEvent rows linked to sleep session and media clip plan.",
            ),
            success_criteria=(
                "Shadow mode records candidates only and never emits red medical alert.",
                "False positives are reviewed before any production alerting decision.",
            ),
        ),
        ExternalValidationItem(
            task_id="APC-T040",
            title="mmWave MQTT device soak",
            resource_type="mmwave_device",
            blocked_by="Requires real Mosquitto broker/device publishing baby/radar/telemetry.",
            commands=(
                "make mmwave-replay",
                "make run-mmwave-worker",
                "make worker-db-smoke-test",
            ),
            evidence_required=(
                "MQTT broker logs showing telemetry from physical device.",
                "sensor_event rows and optional ObservationEvent rows.",
                "At least one soak window with no worker crash.",
            ),
            success_criteria=(
                "Device telemetry ingests continuously.",
                "Single mmWave signal cannot generate red alert.",
            ),
        ),
        ExternalValidationItem(
            task_id="APC-T041",
            title="ESP32C6 PlatformIO compile/flash",
            resource_type="firmware_hardware",
            blocked_by="Requires local PlatformIO toolchain and ESP32C6 hardware.",
            commands=(
                "make firmware-preflight",
                "cd firmware/esp32c6 && pio run",
                "cd firmware/esp32c6 && pio run -t upload",
            ),
            evidence_required=(
                "pio run build log.",
                "pio upload log or serial monitor payload sample.",
                "Local config.h kept out of git.",
            ),
            success_criteria=(
                "Firmware builds and flashes on target board.",
                "Serial/MQTT payload matches expected telemetry JSON shape.",
            ),
        ),
        ExternalValidationItem(
            task_id="APC-T044",
            title="Real backup/NAS restore drill",
            resource_type="nas_restore",
            blocked_by=(
                "Requires real pg_dump output, NAS/media archive, "
                "and disposable restore DB."
            ),
            commands=(
                "make backup-dry-run",
                "make backup-verify-dry-run",
                "pg_restore --list runtime/backups/pg/latest.dump",
                "pg_restore --dbname "
                "postgresql://parenting:parenting@127.0.0.1:5432/parenting_restore "
                "--clean runtime/backups/pg/latest.dump",
            ),
            evidence_required=(
                "pg_dump file and NAS path.",
                "backup manifest verification output.",
                "Disposable DB restore log and db-current output.",
            ),
            success_criteria=(
                "Restore drill completes on disposable DB.",
                "Media archive scope is limited to encrypted files/thumbs.",
            ),
        ),
        ExternalValidationItem(
            task_id="APC-T059",
            title="Seven-night shadow/soak validation",
            resource_type="long_running_soak",
            blocked_by="Requires real 7-night observation window and family-scale soak.",
            commands=(
                "make p0-readiness",
                "make shadow-test",
                "locust -f tests/soak/locustfile.py --host http://127.0.0.1:8000",
            ),
            evidence_required=(
                "Seven-night shadow report.",
                "Soak metrics/logs for API, worker, memory, and file handles.",
                "Reviewed release checklist with all local-only items checked.",
            ),
            success_criteria=(
                "No unreviewed strong alert from shadow signals.",
                "Soak stays within household-scale stability budget.",
            ),
        ),
    ]

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 21:45:00

"""P0 release-readiness aggregate report.

This report consolidates deterministic checks that can run without clinical reviewers,
real Android devices, RTSP cameras, mmWave hardware, FCM credentials, or NAS access.
It intentionally lists those external validation items as remaining blockers instead
of marking them complete.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from firmware.esp32c6.tools.preflight import run_preflight
from server.app.backup.restore_drill import RestoreDrillPlanner
from server.app.backup.verification import BackupManifestVerifier
from server.app.camera.fusion import FusionInput, FusionStateMachine
from server.app.mmwave.frame_parser import parse_jsonl
from server.app.mmwave.replay import replay_mmwave_fixture
from server.app.notification.android_contract import build_android_notification_contract_report
from server.app.notification.escalation_report import simulate_red_alert_escalation
from server.app.ops.deployment_readiness import build_deployment_readiness_report
from server.app.rule_engine.review_packet import build_rule_review_packet
from server.app.sync.e2e_contract import build_android_e2e_contract_report


@dataclass(frozen=True, slots=True)
class P0ReadinessReport:
    automated_status: str
    automated_checks: dict[str, str]
    external_blockers: tuple[str, ...]
    next_commands: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def build_p0_readiness_report(project_root: Path | str = ".") -> P0ReadinessReport:
    root = Path(project_root)
    checks: dict[str, str] = {}
    next_commands = [
        "make rule-review-packet",
        "make android-e2e-contract",
        "make android-notification-contract",
        "make deployment-readiness",
        "make backup-verify-dry-run",
        "make mmwave-replay",
        "make firmware-preflight",
        "make red-alert-sim",
        "make shadow-test",
    ]

    rule_packet = build_rule_review_packet(root)
    checks["rule_review_packet_generated"] = _status(bool(rule_packet.golden_cases))
    checks["rule_golden_cases"] = _status(all(case.passed for case in rule_packet.golden_cases))
    checks["rule_human_blockers_declared"] = _status(bool(rule_packet.blockers))

    android_e2e = build_android_e2e_contract_report(root)
    checks["android_e2e_contract"] = _status(android_e2e.ok)

    android_notification = build_android_notification_contract_report(root)
    checks["android_notification_contract"] = _status(android_notification.ok)

    deployment = build_deployment_readiness_report(root)
    checks["deployment_readiness"] = _status(deployment.ok)

    manifest = RestoreDrillPlanner(restore_root=root / "runtime/restore-drills").manifest(
        pg_dump_path="runtime/backups/pg/latest.dump",
        media_archive_path="runtime/backups/media/latest.tar.gz",
    )
    manifest_writer = RestoreDrillPlanner(restore_root=root / "runtime/restore-drills")
    manifest_path = manifest_writer.write_manifest(manifest)
    backup = BackupManifestVerifier(project_root=root).verify_manifest_file(manifest_path)
    checks["backup_manifest_verifier"] = _status(backup.ok)

    mmwave = replay_mmwave_fixture(root / "tests/fixtures/radar_frames.jsonl")
    checks["mmwave_fixture_replay"] = _status(
        mmwave.total_frames > 0 and mmwave.abnormal_count >= 1
    )

    firmware = run_preflight(root / "firmware/esp32c6")
    checks["firmware_static_preflight"] = _status(firmware.ok)

    red_alert = asyncio.run(simulate_red_alert_escalation())
    checks["red_alert_fake_escalation"] = _status(
        red_alert.trigger_only_payloads and red_alert.acknowledged
    )

    shadow = _shadow_fixture_summary(root / "tests/fixtures/radar_frames.jsonl")
    checks["shadow_harness_no_red"] = _status(
        shadow["total_frames"] > 0
        and shadow["red_count"] == 0
        and shadow["candidate_count"] > 0
    )

    checklist = _read(root / "docs/RELEASE_CHECKLIST_P0.md")
    for keyword in ("FCM", "Camera vendor cloud disabled", "Restore drill"):
        checks[f"release_checklist:{keyword}"] = _status(keyword in checklist)

    automated_ok = all(value == "ok" for value in checks.values())
    return P0ReadinessReport(
        automated_status="ready_for_external_validation" if automated_ok else "failed",
        automated_checks=checks,
        external_blockers=tuple(_external_blockers()),
        next_commands=tuple(next_commands),
    )


def _shadow_fixture_summary(fixture: Path) -> dict[str, int]:
    frames = parse_jsonl(fixture.read_text(encoding="utf-8"))
    fusion = FusionStateMachine()
    candidate_count = 0
    red_count = 0
    for frame in frames:
        decision = fusion.evaluate(
            FusionInput(
                sleep_session_active=True,
                camera_kind="face_covered" if frame.abnormal_event else None,
                camera_confidence=0.9 if frame.abnormal_event else None,
                mmwave_abnormal_event=frame.abnormal_event,
            )
        )
        if decision.shadow_event:
            candidate_count += 1
        if decision.alert_level == "red":
            red_count += 1
    return {"total_frames": len(frames), "candidate_count": candidate_count, "red_count": red_count}


def _external_blockers() -> list[str]:
    return [
        "APC-T022: human review of CN vaccine production schedule.",
        "APC-T023: full WHO LMS growth table import/review.",
        "APC-T038/T039: real RTSP/ISAPI/Fregata/VLM device shadow validation.",
        "APC-T040: real MQTT broker + mmWave device soak.",
        "APC-T041: PlatformIO compile/flash on ESP32C6 hardware.",
        "APC-T044: real pg_dump/NAS/media archive/restore drill on disposable DB.",
        "APC-T059: seven-night shadow/soak run with reviewed false-positive report.",
    ]


def _status(ok: bool) -> str:
    return "ok" if ok else "failed"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 04:48:00

"""Android/PowerSync MVP E2E contract report.

This report is a deterministic substitute for real-device execution. It verifies
that Android offline-first files still expose the required local event schema,
pending drain routes, heartbeat route, and Today pending visibility while server-side
sync contract validation accepts the same shape.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from server.app.sync.service.contract_validator import validate_sync_record

REQUIRED_ANDROID_FILES = (
    "android/src/sync/schema.ts",
    "android/src/sync/pending_sync_drain.ts",
    "android/src/sync/native_sqlite_bridge.ts",
    "android/src/features/quick_record/createLocalEvent.ts",
    "android/src/features/quick_record/copilotFlow.ts",
    "android/android/app/src/main/java/com/aiparentingcopilot/QuickRecordActivity.kt",
    "android/android/app/src/main/java/com/aiparentingcopilot/PendingSyncDrainer.kt",
    "android/android/app/src/main/java/com/aiparentingcopilot/TodayActivity.kt",
)

REQUIRED_COLUMNS = (
    "event_id",
    "baby_id",
    "family_id",
    "user_id",
    "device_id",
    "event_type",
    "client_created_at",
    "start_time",
    "payload",
    "source",
    "confidence",
    "pending_sync",
)


@dataclass(frozen=True, slots=True)
class AndroidE2EContractReport:
    ok: bool
    checks: dict[str, str]
    errors: tuple[str, ...]
    sample_event: dict[str, Any]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def build_android_e2e_contract_report(project_root: Path | str = ".") -> AndroidE2EContractReport:
    root = Path(project_root)
    checks: dict[str, str] = {}
    errors: list[str] = []
    for rel in REQUIRED_ANDROID_FILES:
        _expect((root / rel).exists(), f"file:{rel}", checks, errors)
    schema_text = _read(root / "android/src/sync/schema.ts")
    for column in REQUIRED_COLUMNS:
        _expect(f"'{column}'" in schema_text, f"schema_column:{column}", checks, errors)
    pending_drain = _read(root / "android/src/sync/pending_sync_drain.ts")
    _expect("/api/v1/events" in pending_drain, "ts_drain_events_route", checks, errors)
    _expect("/api/v1/sync/heartbeat" in pending_drain, "ts_drain_heartbeat_route", checks, errors)
    quick_record = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/QuickRecordActivity.kt"
    )
    _expect("insertPending" in quick_record, "native_quick_record_insert_pending", checks, errors)
    _expect(
        "saveFallbackCandidate" in quick_record,
        "native_quick_record_offline_fallback",
        checks,
        errors,
    )
    pending_native = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/PendingSyncDrainer.kt"
    )
    _expect("/api/v1/events" in pending_native, "native_drain_events_route", checks, errors)
    _expect(
        "/api/v1/sync/heartbeat" in pending_native,
        "native_drain_heartbeat_route",
        checks,
        errors,
    )
    today = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/TodayActivity.kt"
    )
    _expect("Pending sync:" in today, "today_pending_visible", checks, errors)
    sample_event = _sample_sync_event()
    try:
        validate_sync_record(sample_event)
        checks["server_sync_contract_sample"] = "ok"
    except Exception as exc:
        checks["server_sync_contract_sample"] = "failed"
        errors.append(f"sample event rejected by server sync contract: {exc}")
    return AndroidE2EContractReport(
        ok=not errors,
        checks=checks,
        errors=tuple(errors),
        sample_event=sample_event,
    )


def _sample_sync_event() -> dict[str, Any]:
    now = datetime(2026, 8, 4, tzinfo=UTC).isoformat()
    return {
        "event_id": "android-e2e-sample-event",
        "baby_id": "baby-e2e",
        "family_id": "family-e2e",
        "user_id": "user-e2e",
        "device_id": "device-e2e",
        "event_type": "feeding",
        "client_created_at": now,
        "start_time": now,
        "payload": {"amount_ml": 90},
        "source": "manual",
        "confidence": 1.0,
        "is_deleted": False,
        "correction_of": None,
    }


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _expect(
    condition: bool,
    check_name: str,
    checks: dict[str, str],
    errors: list[str],
) -> None:
    checks[check_name] = "ok" if condition else "failed"
    if not condition:
        errors.append(f"Android E2E contract failed: {check_name}")

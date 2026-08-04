# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 22:58:00

"""Rule review sign-off validator.

This module validates external reviewer sign-off artifacts for rule packs. It does
not auto-activate production medical content; it gives operators a deterministic
way to detect hash/version mismatches and whether a sign-off is only valid for
shadow/dev review or production release.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from server.app.rule_engine.loader import RulePack, load_rule_pack

DOMAIN_RULE_PACKS = {
    "vaccine": Path("config/rules/vaccine/cn-nip-2024.yaml"),
    "growth": Path("config/rules/growth/who-0-5.yaml"),
    "medication": Path("config/rules/medication/base.yaml"),
    "triage": Path("config/rules/triage/base.yaml"),
}

REQUIRED_CHECKLIST = {
    "vaccine": (
        "official_source_verified",
        "schedule_dates_verified",
        "golden_cases_reviewed",
        "user_copy_reviewed",
    ),
    "growth": (
        "full_who_lms_table_verified",
        "percentile_algorithm_reviewed",
        "golden_cases_reviewed",
        "no_single_point_alert_reviewed",
    ),
    "medication": (
        "clinical_source_verified",
        "dose_formula_reviewed",
        "golden_cases_reviewed",
        "contraindication_copy_reviewed",
    ),
    "triage": (
        "clinical_redlines_verified",
        "danger_signals_reviewed",
        "golden_cases_reviewed",
        "recommended_action_copy_reviewed",
    ),
}


@dataclass(frozen=True, slots=True)
class RuleReviewSignoff:
    domain: str
    region: str
    version: str
    pack_hash: str
    status: str
    scope: str
    reviewer: str
    reviewed_at: str
    checklist: dict[str, bool] = field(default_factory=dict)
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuleReviewSignoff:
        return cls(
            domain=str(data.get("domain", "")),
            region=str(data.get("region", "")),
            version=str(data.get("version", "")),
            pack_hash=str(data.get("pack_hash", "")),
            status=str(data.get("status", "")),
            scope=str(data.get("scope", "")),
            reviewer=str(data.get("reviewer", "")),
            reviewed_at=str(data.get("reviewed_at", "")),
            checklist={str(k): bool(v) for k, v in dict(data.get("checklist", {})).items()},
            notes=str(data.get("notes")) if data.get("notes") is not None else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RuleReviewSignoffResult:
    ok: bool
    domain: str
    scope: str
    pack_hash: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def build_signoff_template(
    domain: str,
    *,
    project_root: Path | str = ".",
    scope: str = "dev_shadow",
) -> RuleReviewSignoff:
    pack = _load_pack(domain, Path(project_root))
    checklist = {key: False for key in REQUIRED_CHECKLIST.get(domain, ("golden_cases_reviewed",))}
    return RuleReviewSignoff(
        domain=pack.domain,
        region=pack.region,
        version=pack.version,
        pack_hash=pack.compute_hash(),
        status="pending",
        scope=scope,
        reviewer="",
        reviewed_at="",
        checklist=checklist,
        notes="Fill reviewer, reviewed_at, checklist and set status=approved when complete.",
    )


def validate_rule_signoff(
    signoff: RuleReviewSignoff,
    *,
    project_root: Path | str = ".",
) -> RuleReviewSignoffResult:
    errors: list[str] = []
    warnings: list[str] = []
    root = Path(project_root)
    try:
        pack = _load_pack(signoff.domain, root)
    except Exception as exc:
        return RuleReviewSignoffResult(
            ok=False,
            domain=signoff.domain,
            scope=signoff.scope,
            pack_hash=signoff.pack_hash,
            errors=(f"rule pack load failed: {exc}",),
        )
    _expect(signoff.status == "approved", "status must be approved", errors)
    _expect(bool(signoff.reviewer), "reviewer is required", errors)
    _expect(bool(signoff.reviewed_at), "reviewed_at is required", errors)
    _expect(signoff.region == pack.region, "region mismatch", errors)
    _expect(signoff.version == pack.version, "version mismatch", errors)
    actual_hash = pack.compute_hash()
    _expect(signoff.pack_hash == actual_hash, "pack_hash mismatch", errors)
    for key in REQUIRED_CHECKLIST.get(signoff.domain, ("golden_cases_reviewed",)):
        _expect(signoff.checklist.get(key) is True, f"checklist missing/false: {key}", errors)
    if signoff.scope == "production":
        if _is_dev_pack(pack):
            errors.append("production signoff cannot approve dev fixture rule pack")
    elif signoff.scope == "dev_shadow":
        warnings.append("dev_shadow signoff is not production approval")
    else:
        errors.append(f"unsupported signoff scope: {signoff.scope}")
    return RuleReviewSignoffResult(
        ok=not errors,
        domain=signoff.domain,
        scope=signoff.scope,
        pack_hash=actual_hash,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def load_signoff_file(path: Path | str) -> RuleReviewSignoff:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("signoff file must contain a JSON object")
    return RuleReviewSignoff.from_dict(data)


def _load_pack(domain: str, root: Path) -> RulePack:
    rel = DOMAIN_RULE_PACKS.get(domain)
    if rel is None:
        raise ValueError(f"unsupported signoff domain: {domain}")
    return load_rule_pack(root / rel)


def _is_dev_pack(pack: RulePack) -> bool:
    haystack = f"{pack.version} {pack.source}".lower()
    return "dev" in haystack or "fixture" in haystack or "requires" in haystack


def _expect(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)

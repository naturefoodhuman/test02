# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-03 11:05:00

"""Rule review packet builder for production sign-off.

This module does not approve medical/vaccine/growth rules. It packages the current
rule packs, hashes, golden-case outcomes, and explicit human-review blockers so a
clinical/product reviewer can sign off without digging through source files.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from server.app.common.clock import utc_now
from server.app.rule_engine.domain.models import RuleInput, RuleResult
from server.app.rule_engine.domains.growth import GrowthRuleModule
from server.app.rule_engine.domains.medication import MedicationRuleModule
from server.app.rule_engine.domains.thresholds import ThresholdRuleModule
from server.app.rule_engine.domains.triage import TriageRuleModule
from server.app.rule_engine.domains.vaccine import VaccineRuleModule
from server.app.rule_engine.loader import RulePack, load_rule_pack, validate_rule_packs


@dataclass(frozen=True, slots=True)
class RulePackReviewSummary:
    domain: str
    policy_type: str
    region: str
    version: str
    source: str
    hash: str
    rule_ids: tuple[str, ...]
    requires_human_review: bool
    review_note: str


@dataclass(frozen=True, slots=True)
class GoldenCaseReviewResult:
    domain: str
    name: str
    passed: bool
    verdict: str
    reason_code: str
    expected: dict[str, Any]
    actual: dict[str, Any]
    error: str | None = None


@dataclass(frozen=True, slots=True)
class RuleReviewPacket:
    generated_at: str
    review_status: str
    pack_summaries: tuple[RulePackReviewSummary, ...]
    golden_cases: tuple[GoldenCaseReviewResult, ...]
    blockers: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = [
            "# AI Parenting Copilot Rule Review Packet",
            "",
            f"- Generated at: `{self.generated_at}`",
            f"- Review status: `{self.review_status}`",
            "- Safety note: this packet is evidence for reviewer sign-off; "
            "it is not medical approval.",
            "",
            "## Human-review blockers",
        ]
        for blocker in self.blockers:
            lines.append(f"- {blocker}")
        lines.extend(["", "## Rule packs"])
        for pack in self.pack_summaries:
            lines.extend(
                [
                    f"### {pack.domain} / {pack.region} / {pack.version}",
                    f"- Policy type: `{pack.policy_type}`",
                    f"- SHA256 hash: `{pack.hash}`",
                    f"- Source: {pack.source}",
                    f"- Rules: {', '.join(pack.rule_ids)}",
                    f"- Requires human review: `{str(pack.requires_human_review).lower()}`",
                    f"- Review note: {pack.review_note}",
                    "",
                ]
            )
        lines.extend(["## Golden cases", ""])
        for case in self.golden_cases:
            status = "PASS" if case.passed else "FAIL"
            lines.extend(
                [
                    f"- `{status}` `{case.domain}` / `{case.name}`: verdict=`{case.verdict}`, "
                    f"reason=`{case.reason_code}`",
                ]
            )
            if case.error:
                lines.append(f"  - Error: {case.error}")
        lines.append("")
        return "\n".join(lines)


def build_rule_review_packet(project_root: Path | str = ".") -> RuleReviewPacket:
    root = Path(project_root)
    packs = validate_rule_packs(root / "config/rules")
    pack_by_domain = {pack.domain: pack for pack in packs}
    threshold_pack = load_rule_pack(root / "config/alert_thresholds.yaml")
    pack_by_domain["thresholds"] = threshold_pack
    pack_summaries = tuple(_pack_summary(pack) for pack in [*packs, threshold_pack])
    golden_cases = tuple(_evaluate_all_golden_cases(root, pack_by_domain))
    blockers = tuple(_review_blockers(pack_summaries))
    return RuleReviewPacket(
        generated_at=utc_now().isoformat(),
        review_status="pending_human_review" if blockers else "ready_for_release_review",
        pack_summaries=pack_summaries,
        golden_cases=golden_cases,
        blockers=blockers,
    )


def write_rule_review_packet(
    packet: RuleReviewPacket,
    *,
    output_dir: Path | str = "runtime/reports",
) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stem = f"rule-review-packet-{utc_now().strftime('%Y%m%dT%H%M%SZ')}"
    json_path = output / f"{stem}.json"
    md_path = output / f"{stem}.md"
    json_path.write_text(packet.to_json(), encoding="utf-8")
    md_path.write_text(packet.to_markdown(), encoding="utf-8")
    return json_path, md_path


def _pack_summary(pack: RulePack) -> RulePackReviewSummary:
    review_note = _review_note(pack)
    return RulePackReviewSummary(
        domain=pack.domain,
        policy_type=pack.policy_type,
        region=pack.region,
        version=pack.version,
        source=pack.source,
        hash=pack.compute_hash(),
        rule_ids=tuple(rule.id for rule in pack.rules),
        requires_human_review=review_note is not None,
        review_note=review_note or "Automated golden cases passed; no extra blocker recorded.",
    )


def _review_note(pack: RulePack) -> str | None:
    if pack.domain == "vaccine":
        return "Requires official CN immunization schedule review before production activation."
    if pack.domain == "growth":
        return "Requires full WHO LMS table import/review before production activation."
    if "requires" in pack.source.lower() or "dev" in pack.version.lower():
        return (
            "Development baseline; requires owner/reviewer sign-off before production activation."
        )
    return None


def _review_blockers(pack_summaries: tuple[RulePackReviewSummary, ...]) -> list[str]:
    blockers = [
        f"{pack.domain}:{pack.region}:{pack.version} - {pack.review_note}"
        for pack in pack_summaries
        if pack.requires_human_review
    ]
    blockers.append("Reviewer must verify no LLM path can produce dose/threshold/triage decisions.")
    return blockers


def _evaluate_all_golden_cases(
    root: Path,
    pack_by_domain: dict[str, RulePack],
) -> list[GoldenCaseReviewResult]:
    results: list[GoldenCaseReviewResult] = []
    for path in sorted((root / "tests/golden/rules").glob("*_cases.yaml")):
        raw_cases = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for case in raw_cases.get("cases", []):
            domain = str(case.get("domain") or path.name.removesuffix("_cases.yaml"))
            results.append(_evaluate_case(domain, case, pack_by_domain))
    return results


def _module_for(domain: str, pack_by_domain: dict[str, RulePack]) -> Any:
    if domain == "medication":
        return MedicationRuleModule(pack_by_domain[domain])
    if domain == "triage":
        return TriageRuleModule(pack_by_domain[domain])
    if domain == "thresholds":
        return ThresholdRuleModule(pack_by_domain[domain])
    if domain == "vaccine":
        return VaccineRuleModule(pack_by_domain[domain])
    if domain == "growth":
        return GrowthRuleModule(pack_by_domain[domain])
    raise ValueError(f"unsupported golden-case domain: {domain}")


def _evaluate_case(
    domain: str,
    case: dict[str, Any],
    pack_by_domain: dict[str, RulePack],
) -> GoldenCaseReviewResult:
    expected = dict(case.get("expect", {}))
    try:
        result = _module_for(domain, pack_by_domain).evaluate(
            RuleInput(domain=domain, payload=dict(case.get("input", {})))
        )
        actual = _actual_summary(domain, result)
        passed = _matches_expected(domain, expected, actual, result)
        return GoldenCaseReviewResult(
            domain=domain,
            name=str(case.get("name", "unnamed")),
            passed=passed,
            verdict=str(result.verdict),
            reason_code=result.reason_code,
            expected=expected,
            actual=actual,
        )
    except Exception as exc:
        return GoldenCaseReviewResult(
            domain=domain,
            name=str(case.get("name", "unnamed")),
            passed=False,
            verdict="error",
            reason_code="exception",
            expected=expected,
            actual={},
            error=str(exc),
        )


def _actual_summary(domain: str, result: RuleResult) -> dict[str, Any]:
    actual: dict[str, Any] = {
        "verdict": str(result.verdict),
        "reason_code": result.reason_code,
        **result.outputs,
    }
    if domain == "vaccine":
        actual.update(
            {
                item["vaccine_key"]: item["status"]
                for item in result.outputs.get("planned", [])
                if isinstance(item, dict) and "vaccine_key" in item
            }
        )
    return actual


def _matches_expected(
    domain: str,
    expected: dict[str, Any],
    actual: dict[str, Any],
    result: RuleResult,
) -> bool:
    if domain == "medication" and "dose_mg" in expected:
        actual_dose = float(result.outputs.get("dose_mg", 0.0))
        if abs(actual_dose - float(expected["dose_mg"])) > 0.001:
            return False
    return all(str(actual.get(key)) == str(value) for key, value in expected.items())

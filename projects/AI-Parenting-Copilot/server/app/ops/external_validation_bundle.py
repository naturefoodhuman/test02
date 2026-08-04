# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-05 01:25:00

"""External validation bundle builder.

A bundle gives the Mac/device operator one directory containing every evidence
and sign-off template needed to close the remaining external APC blockers, plus a
fresh plan/closeout recommendation snapshot. It is intentionally file-only and does
not close tasks automatically.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from server.app.common.clock import utc_now
from server.app.ops.closeout_recommendation import (
    build_closeout_recommendation_report,
    write_closeout_recommendation_report,
)
from server.app.ops.external_evidence import write_evidence_template
from server.app.ops.external_validation import (
    build_external_validation_plan,
    write_external_validation_plan,
)
from server.app.rule_engine.review_signoff import build_signoff_template


@dataclass(frozen=True, slots=True)
class ExternalValidationBundle:
    created_at: str
    output_dir: str
    plan_json: str
    plan_markdown: str
    evidence_templates: tuple[str, ...]
    signoff_templates: tuple[str, ...]
    closeout_recommendation_json: str
    closeout_recommendation_markdown: str
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def build_external_validation_bundle(
    *,
    output_dir: Path | str = "runtime/reports/external-validation-bundle",
) -> ExternalValidationBundle:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    plan = build_external_validation_plan()
    plan_json, plan_md = write_external_validation_plan(plan, output_dir=output)
    evidence_dir = output / "external-evidence"
    evidence_paths = tuple(
        str(write_evidence_template(item.task_id, output_dir=evidence_dir)) for item in plan.items
    )
    signoff_dir = output / "rule-signoffs"
    signoff_dir.mkdir(parents=True, exist_ok=True)
    signoff_paths = tuple(_write_signoff_templates(signoff_dir))
    recommendation = build_closeout_recommendation_report(
        signoff_dir=signoff_dir,
        evidence_dir=evidence_dir,
    )
    recommendation_json, recommendation_md = write_closeout_recommendation_report(
        recommendation,
        output_dir=output,
    )
    bundle = ExternalValidationBundle(
        created_at=utc_now().isoformat(),
        output_dir=str(output),
        plan_json=str(plan_json),
        plan_markdown=str(plan_md),
        evidence_templates=evidence_paths,
        signoff_templates=signoff_paths,
        closeout_recommendation_json=str(recommendation_json),
        closeout_recommendation_markdown=str(recommendation_md),
        notes=(
            "Fill evidence/signoff templates after real local validation.",
            "Run make apc-closeout-gate after templates are completed.",
            "Do not treat generated templates as validation evidence by themselves.",
        ),
    )
    manifest_path = output / "external-validation-bundle.json"
    manifest_path.write_text(bundle.to_json(), encoding="utf-8")
    return bundle


def _write_signoff_templates(output_dir: Path) -> list[str]:
    paths: list[str] = []
    for domain in ("vaccine", "growth"):
        template = build_signoff_template(domain, scope="dev_shadow")
        path = output_dir / f"{domain}-dev-shadow-signoff-template.json"
        path.write_text(
            json.dumps(template.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        paths.append(str(path))
        production_template = build_signoff_template(domain, scope="production")
        production_path = output_dir / f"{domain}-production-signoff-template.json"
        production_path.write_text(
            json.dumps(production_template.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        paths.append(str(production_path))
    return paths

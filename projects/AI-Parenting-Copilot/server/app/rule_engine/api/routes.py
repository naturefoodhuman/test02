# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 13:40:00


"""Rules Admin API in dev/in-memory mode."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import cast

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel

from server.app.common.errors import AppError
from server.app.observability.audit import AuditActor, AuditRecord, AuditSink
from server.app.rule_engine.evidence_repo import (
    EvidencePolicyRecord,
    InMemoryEvidencePolicyRepository,
)
from server.app.rule_engine.loader import RulePack, load_rule_pack, validate_rule_packs

router = APIRouter(prefix="/api/v1/rules", tags=["rules"])


class RulePackPathRequest(BaseModel):
    path: str


def _require_admin(role: str | None) -> None:
    if role != "Admin":
        raise AppError("Admin role required", code="PERMISSION_DENIED", status_code=403)


def _repo(request: Request) -> InMemoryEvidencePolicyRepository:
    repo = getattr(request.app.state, "evidence_policy_repo", None)
    if repo is None:
        raise AppError(
            "EvidencePolicy repo is not configured",
            code="RULE_REPO_UNAVAILABLE",
            status_code=500,
        )
    return cast(InMemoryEvidencePolicyRepository, repo)


async def _audit(request: Request, action: str, record: EvidencePolicyRecord) -> None:
    sink = getattr(request.app.state, "audit_sink", None)
    if sink is None:
        return
    audit_sink = cast(AuditSink, sink)
    await audit_sink.record(
        AuditRecord(
            actor=AuditActor(actor_kind="admin"),
            action=action,
            resource=f"evidence_policy:{record.policy_type}:{record.version}",
            after=asdict(record),
        )
    )


@router.get("/validate")
async def validate_rules(root: str = "config/rules") -> dict[str, object]:
    packs = validate_rule_packs(Path(root))
    return {"count": len(packs), "packs": [pack.model_dump(mode="json") for pack in packs]}


@router.post("/activate", response_model=dict[str, object])
async def activate_rule_pack(
    payload: RulePackPathRequest,
    request: Request,
    x_role: str | None = Header(default=None, alias="x-role"),
) -> dict[str, object]:
    _require_admin(x_role)
    pack: RulePack = load_rule_pack(Path(payload.path))
    record = _repo(request).activate(pack)
    await _audit(request, "rule.activate", record)
    return {"activated": asdict(record)}

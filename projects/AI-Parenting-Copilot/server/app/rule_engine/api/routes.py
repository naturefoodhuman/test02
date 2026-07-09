# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 13:40:00


"""Rules Admin API in dev/in-memory mode."""

from __future__ import annotations

import inspect
from dataclasses import asdict
from pathlib import Path
from typing import cast

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel

from server.app.common.errors import AppError
from server.app.observability.request_audit import record_request_audit
from server.app.rule_engine.evidence_repo import (
    InMemoryEvidencePolicyRepository,
)
from server.app.rule_engine.loader import RulePack, load_rule_pack, validate_rule_packs
from server.app.rule_engine.sqlalchemy_evidence_repo import SQLAlchemyEvidencePolicyRepository

router = APIRouter(prefix="/api/v1/rules", tags=["rules"])


class RulePackPathRequest(BaseModel):
    path: str


def _require_admin(role: str | None) -> None:
    if role != "Admin":
        raise AppError("Admin role required", code="PERMISSION_DENIED", status_code=403)


def _repo(
    request: Request,
) -> InMemoryEvidencePolicyRepository | SQLAlchemyEvidencePolicyRepository:
    db_session = getattr(request.state, "db_session", None)
    if db_session is not None:
        return SQLAlchemyEvidencePolicyRepository(db_session)
    repo = getattr(request.app.state, "evidence_policy_repo", None)
    if repo is None:
        raise AppError(
            "EvidencePolicy repo is not configured",
            code="RULE_REPO_UNAVAILABLE",
            status_code=500,
        )
    return cast(InMemoryEvidencePolicyRepository, repo)


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
    record_or_awaitable = _repo(request).activate(pack)
    if inspect.isawaitable(record_or_awaitable):
        record = await record_or_awaitable
    else:
        record = record_or_awaitable
    await record_request_audit(
        request,
        actor_kind="admin",
        action="rule.activate",
        resource=f"evidence_policy:{record.policy_type}:{record.version}",
        after=asdict(record),
    )
    return {"activated": asdict(record)}

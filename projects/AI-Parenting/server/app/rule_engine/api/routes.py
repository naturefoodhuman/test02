# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
#
# app/rule_engine/api/routes.py —— Rules Admin API 路由（验证/上传/激活/列表 + 审计）。
# 依据：ENGINEERING_DESIGN §13.2（新增 Rule Pack 流程：YAML→validate→activate→audit）；
#       ARCHITECTURE_FINAL §18（规则库版本化）、§19（权限 rule:configure/rule:activate 仅 Admin）；
#       TASK_BACKLOG APC-T019（/api/v1/rules；规则变更仅 Admin；激活新版本旧版本 effective_to 自动关闭；每次变更写 audit_log）。
# 设计：API 前缀 /api/v1/rules；路由只做 HTTP 适配（请求/响应模型 + 调用 evidence_repo + RBAC + audit）。
#       - POST /policies:validate：校验规则包 YAML（Pydantic + hash，不入库）。
#       - POST /policies：上传规则包（validate + upsert 写入新版本，需 rule:configure，audit）。
#       - POST /policies:activate：激活指定版本（旧版本 effective_to 自动关闭，需 rule:activate，audit）。
#       - GET /policies：列出版本（当前生效 + 历史，只读，需 rule:configure）。
#       RulesContext（EvidencePolicyRepository + AuditService 共享请求 session，§10.4 不可绕过）。
# 边界：路由不感知 DB；版本化/缓存失效在 evidence_repo；RBAC 在 AuthService.authorize。

"""Rules Admin API 路由（验证 / 上传 / 激活 / 列表 + 审计）。

端点（前缀 ``/api/v1/rules``，架构 §18/§19/§13.2）：
    - ``POST /policies:validate``：校验规则包 YAML（Pydantic + hash，不入库；需 rule:configure）。
    - ``POST /policies``：上传规则包（validate + upsert 写入新版本；需 rule:configure；audit）。
    - ``POST /policies:activate``：激活指定版本（旧版本 effective_to 自动关闭；需 rule:activate；audit）。
    - ``GET /policies``：列出版本（当前生效 + 历史；需 rule:configure）。

规则变更仅 Admin（架构 §19：``rule:configure`` / ``rule:activate`` 仅 Admin）。
mutating 操作（上传/激活）接 ``AuditService`` 留痕（§10.4 不可绕过），与
``EvidencePolicyRepository`` 共享同一请求 session（``RulesContext``），避免 audit 与
规则写入跨 session 的不一致窗口。路由只做 HTTP 适配；版本化/缓存失效在
``SqlAlchemyEvidencePolicyRepository``；RBAC 在 ``AuthService.authorize``（架构 §5 分层）。
"""

from __future__ import annotations

from typing import Annotated

import yaml
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field

from ...auth.domain import Principal
from ...auth.service.auth_service import AuthService
from ...common.errors import ValidationError
from ...di import RulesContext, get_principal_dep, get_rules_context_dep
from ..domain.models import RulePack
from ..evidence_repo import SqlAlchemyEvidencePolicyRepository

router = APIRouter(prefix="/api/v1/rules", tags=["rules"])

# 依赖别名（Annotated 风格，避免 ruff B008）。
RulesContextDep = Annotated[RulesContext, Depends(get_rules_context_dep)]
PrincipalDep = Annotated[Principal, Depends(get_principal_dep)]


# ---- 请求/响应模型 ----


class PolicyYAMLRequest(BaseModel):
    """上传/校验规则包请求（原始 YAML 文本）。"""

    model_config = ConfigDict(extra="forbid")

    yaml: str = Field(description="规则包 YAML 文本（符合 RulePack schema）")


class ValidatePolicyResponse(BaseModel):
    """校验规则包响应（不入库）。"""

    model_config = ConfigDict(extra="forbid")

    ok: bool = True
    policy_type: str
    region: str
    version: int
    rules_count: int
    hash: str


class PolicyResponse(BaseModel):
    """规则版本响应。"""

    model_config = ConfigDict(extra="forbid")

    id: str
    policy_type: str
    region: str
    version: int
    effective_from: str
    effective_to: str | None
    source: str
    hash: str
    is_current: bool


class ActivateRequest(BaseModel):
    """激活规则版本请求。"""

    model_config = ConfigDict(extra="forbid")

    policy_type: str = Field(description="策略类型")
    region: str = Field(default="CN", description="区域")
    version: int = Field(description="要激活的版本号")


# ---- 辅助 ----


def _parse_pack(yaml_text: str) -> RulePack:
    """解析 YAML 文本 → RulePack（Pydantic 校验 + hash）。

    非法 YAML/非 mapping/校验失败抛 ``ValidationError``（400，由全局处理器映射）。
    """
    try:
        raw = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise ValidationError(f"invalid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValidationError("rule pack YAML must be a mapping")
    # 复用 loader 的 hash 计算（canonical JSON + datetime ISO）。
    from ..loader import _compute_hash

    computed = _compute_hash(raw)
    raw["hash"] = computed
    try:
        return RulePack.model_validate(raw)
    except Exception as exc:  # Pydantic ValidationError 等
        raise ValidationError(f"rule pack schema invalid: {exc}") from exc


def _map_repo_error(exc: ValueError) -> None:
    """把 evidence_repo 的 ValueError（递增失败/已存在/未找到）映射为 ValidationError（400）。

    evidence_repo 用 ValueError 表达业务约束（version 递增、UNIQUE、未找到）；
    路由层统一映射为 400（§9.1 输入校验失败），保留原始消息供定位。
    """
    raise ValidationError(str(exc)) from exc


def _to_response(row, *, is_current: bool | None = None) -> PolicyResponse:
    """ORM EvidencePolicy → PolicyResponse。"""
    eff_to = row.effective_to.isoformat() if row.effective_to is not None else None
    cur = is_current if is_current is not None else (row.effective_to is None)
    return PolicyResponse(
        id=row.id,
        policy_type=row.policy_type,
        region=row.region,
        version=row.version,
        effective_from=row.effective_from.isoformat(),
        effective_to=eff_to,
        source=row.source,
        hash=row.hash,
        is_current=cur,
    )


# ---- 路由 ----


@router.post(
    "/policies:validate",
    response_model=ValidatePolicyResponse,
    status_code=status.HTTP_200_OK,
)
async def validate_policy(
    payload: PolicyYAMLRequest,
    principal: PrincipalDep,
    ctx: RulesContextDep,
) -> ValidatePolicyResponse:
    """校验规则包 YAML（不入库；需 rule:configure）。

    解析 YAML → RulePack（Pydantic 校验 + hash），返回校验摘要。不写 DB。
    """
    AuthService.authorize(principal, "rule:configure")
    pack = _parse_pack(payload.yaml)
    return ValidatePolicyResponse(
        policy_type=pack.policy_type,
        region=pack.region,
        version=pack.version,
        rules_count=len(pack.rules),
        hash=pack.hash or "",
    )


@router.post(
    "/policies",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_policy(
    payload: PolicyYAMLRequest,
    principal: PrincipalDep,
    ctx: RulesContextDep,
) -> PolicyResponse:
    """上传规则包（validate + upsert 写入新版本；需 rule:configure；audit）。

    version 严格递增校验在 evidence_repo（架构 §18）；旧生效版本 effective_to 自动关闭
    （§13.2）。写入后缓存失效（§11 杜绝 stale rule）。审计记录变更人/版本。
    """
    AuthService.authorize(principal, "rule:configure")
    pack = _parse_pack(payload.yaml)
    try:
        row = await ctx.evidence_repo.upsert(pack)
    except ValueError as exc:
        _map_repo_error(exc)
    await ctx.audit_service.append(
        actor=principal.user_id,
        action="rule.upload",
        resource=f"evidence_policy/{pack.policy_type}/{pack.region}@v{pack.version}",
        after={
            "policy_type": pack.policy_type,
            "region": pack.region,
            "version": pack.version,
            "hash": pack.hash,
        },
        rule_version=f"{pack.policy_type}@{pack.version}",
    )
    return _to_response(row, is_current=True)


@router.post(
    "/policies:activate",
    response_model=PolicyResponse,
    status_code=status.HTTP_200_OK,
)
async def activate_policy(
    payload: ActivateRequest,
    principal: PrincipalDep,
    ctx: RulesContextDep,
) -> PolicyResponse:
    """激活指定规则版本（旧版本 effective_to 自动关闭；需 rule:activate；audit）。

    事务内：旧生效版本关闭 + 目标版本 effective_to 置 NULL（evidence_repo.activate）。
    审计记录变更人/激活版本。
    """
    AuthService.authorize(principal, "rule:activate")
    try:
        row = await ctx.evidence_repo.activate(payload.policy_type, payload.region, payload.version)
    except ValueError as exc:
        _map_repo_error(exc)
    await ctx.audit_service.append(
        actor=principal.user_id,
        action="rule.activate",
        resource=f"evidence_policy/{payload.policy_type}/{payload.region}@v{payload.version}",
        after={
            "policy_type": payload.policy_type,
            "region": payload.region,
            "version": payload.version,
            "activated": True,
        },
        rule_version=f"{payload.policy_type}@{payload.version}",
    )
    return _to_response(row, is_current=True)


@router.get(
    "/policies",
    response_model=list[PolicyResponse],
    status_code=status.HTTP_200_OK,
)
async def list_policies(
    principal: PrincipalDep,
    ctx: RulesContextDep,
    policy_type: Annotated[str | None, Query(description="按策略类型过滤")] = None,
    region: Annotated[str | None, Query(description="按区域过滤")] = None,
) -> list[PolicyResponse]:
    """列出规则版本（当前生效 + 历史；需 rule:configure）。

    支持按 policy_type / region 过滤。is_current 标记当前生效版本（effective_to IS NULL）。
    """
    AuthService.authorize(principal, "rule:configure")
    assert isinstance(ctx.evidence_repo, SqlAlchemyEvidencePolicyRepository)
    rows = await ctx.evidence_repo.list_policies(policy_type=policy_type, region=region)
    return [_to_response(r) for r in rows]


__all__ = ["RulesContext", "router"]

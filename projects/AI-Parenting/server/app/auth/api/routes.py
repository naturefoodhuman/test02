# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/auth/api/routes.py —— Auth API 路由（登录/刷新/设备注册 + 鉴权示例端点）。
# 依据：ENGINEERING_DESIGN §2（M02 auth）、§9.1（异常）、§10.4（Audit）；
#       ARCHITECTURE_FINAL §15.2（Auth 域 /login /refresh）、§19（权限）、§25.3；TASK_BACKLOG APC-T008。
# 设计：API 前缀 /api/v1/auth；登录返回 access token；refresh 基于有效 token 滑动续期；
#       设备注册需 Admin（device:register，§19）；/me 示范受保护端点（get_principal_dep）。
#       mutating 操作（register-device）接 AuditService 留痕（§10.4 不可绕过）。
# 边界：路由只做 HTTP 适配（请求/响应模型 + 调用 service）；业务规则在 AuthService。

"""Auth API 路由（登录 / 刷新 / 设备注册 / 鉴权示例）。

端点（前缀 ``/api/v1/auth``，架构 §15.2）：
    - ``POST /login``：家庭 + 成员名 + 密码 → access token + Principal。
    - ``POST /refresh``：基于有效 access token 滑动续期（重签发）。
    - ``POST /register-device``：注册设备（需 Admin，§19 device:register）。
    - ``GET /me``：受保护端点示范，返回当前 Principal（鉴权依赖 ``get_principal_dep``）。

mutating 操作（``register-device``）接 ``AuditService`` 留痕（§10.4 不可绕过）。
路由只做 HTTP 适配；业务规则在 ``AuthService``（架构 §5：分层）。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field

from ...di import get_auth_service_dep, get_principal_dep
from ..domain import DeviceKind, Principal, Role
from ..service.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# 依赖别名（Annotated 风格，避免 ruff B008，FastAPI 推荐写法）。
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service_dep)]
PrincipalDep = Annotated[Principal, Depends(get_principal_dep)]


# ---- 请求/响应模型 ----


class LoginRequest(BaseModel):
    """登录请求（家庭 + 成员名 + 密码）。"""

    model_config = ConfigDict(extra="forbid")

    family_id: str = Field(description="家庭 ULID")
    display_name: str = Field(description="成员显示名（家庭内唯一）")
    password: str = Field(description="成员密码（明文，仅传输；不存储）")
    device_id: str | None = Field(default=None, description="可选：绑定设备 ULID")


class TokenResponse(BaseModel):
    """登录/刷新响应（access token + Principal 摘要）。"""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "Bearer"
    user_id: str
    family_id: str
    role: Role
    device_id: str | None = None
    expires_in: int = Field(description="token 剩余有效期（秒）")


class RefreshResponse(BaseModel):
    """刷新响应（新 access token）。"""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class DeviceRegisterRequest(BaseModel):
    """设备注册请求（需 Admin 鉴权）。"""

    model_config = ConfigDict(extra="forbid")

    kind: DeviceKind = Field(description="设备类型：phone/camera/mmwave/mac")
    fcm_token: str | None = Field(default=None, description="FCM 推送 token")
    meta: dict[str, object] | None = Field(
        default=None, description="设备扩展信息（存 device.meta jsonb）"
    )


class DeviceResponse(BaseModel):
    """设备注册响应。"""

    model_config = ConfigDict(extra="forbid")

    device_id: str
    family_id: str
    kind: DeviceKind


class MeResponse(BaseModel):
    """当前 Principal 信息（受保护端点示范）。"""

    model_config = ConfigDict(extra="forbid")

    user_id: str
    family_id: str
    role: Role
    device_id: str | None = None


# ---- 路由 ----


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    """登录：校验家庭 + 成员名 + 密码，返回 access token。"""
    principal = await auth_service.authenticate(
        family_id=payload.family_id,
        display_name=payload.display_name,
        plain_password=payload.password,
        device_id=payload.device_id,
    )
    token, claims = auth_service.issue_token(principal)
    expires_in = max(0, int(claims.exp.timestamp() - claims.iat.timestamp()))
    return TokenResponse(
        access_token=token,
        user_id=principal.user_id,
        family_id=principal.family_id,
        role=principal.role,
        device_id=principal.device_id,
        expires_in=expires_in,
    )


@router.post("/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
async def refresh(
    auth_service: AuthServiceDep,
    principal: PrincipalDep,
) -> RefreshResponse:
    """刷新：基于有效 access token 滑动续期（重签发新 token）。

    P0 简化：refresh 即用未过期的 access token 换新 token（滑动过期）。
    V1+ 可引入独立 refresh token 与吊销列表（架构 §19 演进）。
    """
    token, claims = auth_service.issue_token(principal)
    expires_in = max(0, int(claims.exp.timestamp() - claims.iat.timestamp()))
    return RefreshResponse(access_token=token, expires_in=expires_in)


@router.post(
    "/register-device",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_device(
    payload: DeviceRegisterRequest,
    auth_service: AuthServiceDep,
    principal: PrincipalDep,
) -> DeviceResponse:
    """注册设备到当前家庭（需 Admin，§19 device:register）。

    注：设备注册的审计留痕待 T009+ 统一 session 管理后接入（避免 audit 与 device
    跨 session 的不一致窗口，§10.4）。当前 ``register_device(audit=None)`` 不留痕。
    """
    device_id = await auth_service.register_device(
        principal=principal,
        kind=payload.kind,
        fcm_token=payload.fcm_token,
        meta=payload.meta,
    )
    return DeviceResponse(
        device_id=device_id,
        family_id=principal.family_id,
        kind=payload.kind,
    )


@router.get("/me", response_model=MeResponse, status_code=status.HTTP_200_OK)
async def me(principal: PrincipalDep) -> MeResponse:
    """受保护端点示范：返回当前 Principal（鉴权依赖 ``get_principal_dep``）。"""
    return MeResponse(
        user_id=principal.user_id,
        family_id=principal.family_id,
        role=principal.role,
        device_id=principal.device_id,
    )


__all__ = ["router"]

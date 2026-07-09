# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 01:15:00


"""Auth API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel, Field

from server.app.auth.domain.models import DeviceKind, Role
from server.app.auth.infra.sqlalchemy_repository import SQLAlchemyAuthRepository
from server.app.auth.service.auth_service import AuthService
from server.app.common.errors import AppError
from server.app.observability.request_audit import record_request_audit

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class InitFamilyRequest(BaseModel):
    family_name: str = Field(min_length=1)
    admin_display_name: str = Field(min_length=1)
    admin_secret: str = Field(min_length=6)
    timezone: str = "Asia/Shanghai"


class LoginRequest(BaseModel):
    family_id: str
    display_name: str
    secret: str
    device_id: str | None = None


class RegisterDeviceRequest(BaseModel):
    kind: DeviceKind
    name: str | None = None
    fcm_token: str | None = None
    meta: dict[str, object] = Field(default_factory=dict)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    family_id: str
    role: Role
    device_id: str | None = None


class InitFamilyResponse(BaseModel):
    family_id: str
    admin_user_id: str
    access_token: str
    token_type: str = "bearer"


class DeviceResponse(BaseModel):
    device_id: str
    family_id: str
    user_id: str | None
    kind: DeviceKind


def _auth_service(request: Request) -> AuthService:
    service = getattr(request.app.state, "auth_service", None)
    if not isinstance(service, AuthService):
        raise AppError(
            "Auth service is not configured",
            code="AUTH_SERVICE_UNAVAILABLE",
            status_code=500,
        )
    db_session = getattr(request.state, "db_session", None)
    if db_session is not None:
        return AuthService(
            SQLAlchemyAuthRepository(db_session),
            service.jwt_service,
            service.password_hasher,
        )
    return service


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AppError("Bearer token required", code="AUTH_REQUIRED", status_code=401)
    return authorization.split(" ", 1)[1]


@router.post("/init-family", response_model=InitFamilyResponse)
async def init_family(payload: InitFamilyRequest, request: Request) -> InitFamilyResponse:
    service = _auth_service(request)
    family, admin = await service.create_family_with_admin(
        family_name=payload.family_name,
        admin_display_name=payload.admin_display_name,
        admin_secret=payload.admin_secret,
        timezone=payload.timezone,
    )
    login = await service.authenticate(
        family_id=family.id,
        display_name=admin.display_name,
        secret=payload.admin_secret,
    )
    await record_request_audit(
        request,
        action="auth.init_family",
        resource=f"family:{family.id}",
        after={"family_id": family.id, "admin_user_id": admin.id},
    )
    return InitFamilyResponse(
        family_id=family.id,
        admin_user_id=admin.id,
        access_token=login.access_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request) -> TokenResponse:
    result = await _auth_service(request).authenticate(
        family_id=payload.family_id,
        display_name=payload.display_name,
        secret=payload.secret,
        device_id=payload.device_id,
    )
    principal = result.principal
    return TokenResponse(
        access_token=result.access_token,
        user_id=principal.user_id,
        family_id=principal.family_id,
        role=principal.role,
        device_id=principal.device_id,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> TokenResponse:
    service = _auth_service(request)
    principal = await service.principal_from_token(_bearer_token(authorization))
    token = service.jwt_service.issue(
        user_id=principal.user_id,
        family_id=principal.family_id,
        role=principal.role.value,
        device_id=principal.device_id,
    )
    return TokenResponse(
        access_token=token,
        user_id=principal.user_id,
        family_id=principal.family_id,
        role=principal.role,
        device_id=principal.device_id,
    )


@router.get("/me", response_model=TokenResponse)
async def me(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> TokenResponse:
    service = _auth_service(request)
    principal = await service.principal_from_token(_bearer_token(authorization))
    return TokenResponse(
        access_token="",
        user_id=principal.user_id,
        family_id=principal.family_id,
        role=principal.role,
        device_id=principal.device_id,
    )


@router.post("/devices/register", response_model=DeviceResponse)
async def register_device(
    payload: RegisterDeviceRequest,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> DeviceResponse:
    service = _auth_service(request)
    principal = await service.principal_from_token(_bearer_token(authorization))
    device = await service.register_device(
        principal=principal,
        kind=payload.kind,
        name=payload.name,
        fcm_token=payload.fcm_token,
        meta=payload.meta,
    )
    await record_request_audit(
        request,
        action="auth.device_register",
        resource=f"device:{device.id}",
        after={"device_id": device.id, "family_id": device.family_id},
    )
    return DeviceResponse(
        device_id=device.id,
        family_id=device.family_id,
        user_id=device.user_id,
        kind=device.kind,
    )

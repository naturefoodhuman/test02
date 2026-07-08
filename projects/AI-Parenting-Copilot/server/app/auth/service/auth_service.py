# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 01:15:00


"""Auth/RBAC application service."""

from __future__ import annotations

from dataclasses import dataclass

from server.app.auth.domain.models import Device, DeviceKind, Family, Principal, Role, User
from server.app.auth.infra.repository import AuthRepository
from server.app.auth.service.jwt_service import JWTService
from server.app.auth.service.passwords import PasswordHasher
from server.app.common.errors import AppError


class AuthError(AppError):
    status_code = 401
    code = "AUTH_FAILED"


class PermissionDenied(AppError):
    status_code = 403
    code = "PERMISSION_DENIED"


@dataclass(frozen=True)
class LoginResult:
    access_token: str
    principal: Principal


class AuthService:
    """Pure Auth/RBAC service over an injected repository."""

    def __init__(
        self,
        repository: AuthRepository,
        jwt_service: JWTService,
        password_hasher: PasswordHasher | None = None,
    ) -> None:
        self.repository = repository
        self.jwt_service = jwt_service
        self.password_hasher = password_hasher or PasswordHasher()

    async def create_family_with_admin(
        self,
        *,
        family_name: str,
        admin_display_name: str,
        admin_secret: str,
        timezone: str = "Asia/Shanghai",
    ) -> tuple[Family, User]:
        family = await self.repository.add_family(Family(name=family_name, timezone=timezone))
        user = User(
            family_id=family.id,
            display_name=admin_display_name,
            role=Role.ADMIN,
            auth_hash=self.password_hasher.hash_secret(admin_secret),
        )
        return family, await self.repository.add_user(user)

    async def authenticate(
        self,
        *,
        family_id: str,
        display_name: str,
        secret: str,
        device_id: str | None = None,
    ) -> LoginResult:
        user = await self.repository.get_user_by_display_name(family_id, display_name)
        if user is None or not user.auth_hash:
            raise AuthError("Invalid credentials")
        if not self.password_hasher.verify_secret(secret, user.auth_hash):
            raise AuthError("Invalid credentials")
        principal = Principal(
            user_id=user.id,
            family_id=user.family_id,
            role=user.role,
            device_id=device_id,
        )
        return LoginResult(
            access_token=self.jwt_service.issue(
                user_id=user.id,
                family_id=user.family_id,
                role=user.role.value,
                device_id=device_id,
            ),
            principal=principal,
        )

    async def principal_from_token(self, token: str) -> Principal:
        claims = self.jwt_service.parse(token)
        return Principal(
            user_id=claims.user_id,
            family_id=claims.family_id,
            role=Role(claims.role),
            device_id=claims.device_id,
        )

    def require_roles(self, principal: Principal, allowed: set[Role]) -> None:
        if principal.role not in allowed:
            raise PermissionDenied(
                "Role is not allowed for this operation",
                evidence={
                    "role": principal.role.value,
                    "allowed": sorted(role.value for role in allowed),
                },
            )

    async def register_device(
        self,
        *,
        principal: Principal,
        kind: DeviceKind,
        name: str | None = None,
        fcm_token: str | None = None,
        meta: dict[str, object] | None = None,
    ) -> Device:
        self.require_roles(principal, {Role.ADMIN, Role.CAREGIVER, Role.SYSTEM})
        return await self.repository.add_device(
            Device(
                family_id=principal.family_id,
                user_id=principal.user_id,
                kind=kind,
                name=name,
                fcm_token=fcm_token,
                meta=dict(meta or {}),
            )
        )

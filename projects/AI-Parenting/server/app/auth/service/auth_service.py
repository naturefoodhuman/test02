# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/auth/service/auth_service.py —— Auth 用例服务（登录/RBAC 判定/家庭与用户创建）。
# 依据：ENGINEERING_DESIGN §2（M02 auth）、§5（Protocol+DI）、§9.1（AuthError/ForbiddenError）、
#       §10.4（Audit，mutating 留痕）、§19（权限体系）、§20（安全）；ARCHITECTURE_FINAL §19；
#       TASK_BACKLOG APC-T007（角色 Admin/Caregiver/Viewer/System；P0 Admin 完整；密码不得明文；
#       JWT 含 user_id/family_id/role/device_id；非授权角色被拒）。
# 设计：用例层，依赖注入 UserRepository/PasswordHasher/JwtService/Clock（架构 §5：Protocol+DI）。
#       事务边界在本层：mutating 方法 flush 后由调用方（gateway 依赖）commit，或显式 commit。
#       RBAC：authorize(principal, action) deny → ForbiddenError（403）；can() 非抛出版。
#       审计：mutating 方法接可选 audit: AuditService | None；提供则 append（§10.4 不可绕过），
#       不提供则跳过（T007 无 API 层；T008 gateway 注入 AuditService 启用留痕）。
# 边界：不感知 HTTP；不签发 token（issue_token 委托 JwtService）；不哈希（委托 PasswordHasher）。

"""Auth 用例服务（登录 / RBAC 判定 / 家庭与用户创建）。

架构（ENGINEERING_DESIGN §5）：用例层依赖注入 Protocol 实现，测试可注入替身。
本服务编排 ``UserRepository`` / ``PasswordHasher`` / ``JwtService`` / ``Clock``，
事务边界在本层（mutating 方法 flush，commit 由调用方决定或显式调用）。

RBAC（架构 §19 / TASK_BACKLOG APC-T007）：
    - ``authorize(principal, action)``：deny 抛 ``ForbiddenError``（403）。
    - ``can(principal, action)``：非抛出版，供条件分支。
    - 权限表在 ``domain.permissions_for``；未列出动作默认 deny（最小权限）。

审计（§10.4 不可绕过）：mutating 方法接可选 ``audit: AuditService | None``；
提供则 ``append`` 留痕，不提供则跳过。T008 的 gateway 层注入 ``AuditService`` 启用留痕。
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ...common.clock import Clock
from ...common.errors import AuthError, ConflictError, ForbiddenError, NotFoundError
from ...common.ids import new_id
from ...observability.audit import AuditService
from ..domain import (
    DeviceKind,
    DeviceRepository,
    JwtService,
    PasswordHasher,
    Principal,
    Role,
    TokenClaims,
    UserRepository,
    permissions_for,
)


class AuthService:
    """Auth 用例服务（登录 / RBAC / 家庭与用户创建 / 设备注册）。

    生命周期：请求作用域（依赖 ``UserRepository`` 持有请求级 ``AsyncSession``）；
    ``PasswordHasher`` / ``JwtService`` 为无状态单例，由 DI 容器注入。
    ``device_repository`` 可选（T008 设备注册；不传则 ``register_device`` 抛 RuntimeError）。
    ``session`` 可选（mutating 方法成功后 commit；Fake 替身测试不传则跳过 commit）。
    事务边界在 service 层（架构 §5.2）：mutating 方法 flush 后由本服务 commit。
    """

    def __init__(
        self,
        *,
        repository: UserRepository,
        password_hasher: PasswordHasher,
        jwt_service: JwtService,
        clock: Clock,
        access_ttl_seconds: int,
        device_repository: DeviceRepository | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        self._repo = repository
        self._hasher = password_hasher
        self._jwt = jwt_service
        self._clock = clock
        self._access_ttl = timedelta(seconds=access_ttl_seconds)
        self._device_repo = device_repository
        self._session = session

    async def _commit(self) -> None:
        """提交事务（若有 session）；Fake 替身测试无 session 时跳过。"""
        if self._session is not None:
            await self._session.commit()

    # ---- 鉴权（登录）----

    async def authenticate(
        self,
        *,
        family_id: str,
        display_name: str,
        plain_password: str,
        device_id: str | None = None,
    ) -> Principal:
        """校验家庭 + 成员名 + 密码，返回 ``Principal``（鉴权产物）。

        家庭不存在 → ``NotFoundError``；成员不存在或密码不符 → ``AuthError``（401，
        不区分"用户不存在"与"密码错"以防用户枚举，§20 安全）。
        """
        family = await self._repo.get_family(family_id)
        if family is None:
            raise NotFoundError("Family not found", evidence={"family_id": family_id})

        user = await self._repo.get_user_by_family(family_id, display_name)
        # 用户不存在与密码错统一返回 AuthError（防用户枚举）。
        if user is None or not self._hasher.verify(plain_password, user.auth_hash):
            raise AuthError("Invalid credentials")

        return Principal(
            user_id=user.id,
            family_id=user.family_id,
            role=Role(user.role),
            device_id=device_id,
        )

    def issue_token(self, principal: Principal) -> tuple[str, TokenClaims]:
        """为 ``Principal`` 签发 JWT，返回 ``(token, claims)``。"""
        now = self._clock.now()
        claims = TokenClaims(
            user_id=principal.user_id,
            family_id=principal.family_id,
            role=principal.role,
            device_id=principal.device_id,
            iat=now,
            exp=now + self._access_ttl,
            jti=new_id(),
        )
        token = self._jwt.issue(claims)
        return token, claims

    def authenticate_token(self, token: str) -> Principal:
        """解析 JWT 并返回 ``Principal``（gateway 鉴权依赖用）。

        解析失败（签名/过期/格式）由 ``JwtService`` 抛 ``AuthError`` 子类（401）。
        """
        claims = self._jwt.parse(token)
        return Principal(
            user_id=claims.user_id,
            family_id=claims.family_id,
            role=claims.role,
            device_id=claims.device_id,
        )

    # ---- RBAC 判定（架构 §19）----

    @staticmethod
    def can(principal: Principal, action: str) -> bool:
        """角色是否允许执行 ``action``（非抛出版）。"""
        return action in permissions_for(principal.role)

    @classmethod
    def authorize(cls, principal: Principal, action: str) -> None:
        """RBAC 判定；deny 抛 ``ForbiddenError``（403）。

        未列出的动作默认 deny（最小权限，``domain.permissions_for`` 未列出返回空集）。
        """
        if not cls.can(principal, action):
            raise ForbiddenError(
                f"Role {principal.role.value} is not permitted to {action}",
                evidence={"role": principal.role.value, "action": action},
            )

    # ---- 家庭与用户创建（T007 验收：可创建 family/user）----

    async def create_family(
        self,
        *,
        name: str,
        timezone: str = "Asia/Shanghai",
        audit: AuditService | None = None,
    ) -> str:
        """创建家庭，返回家庭 id（ULID）。

        事务：flush 后由调用方 commit（或显式 ``commit``）；本方法不 commit。
        审计：提供 ``audit`` 则 append（§10.4）；不提供则跳过（T008 gateway 注入启用）。
        """
        family = await self._repo.create_family(name, timezone)
        if audit is not None:
            await audit.append(
                actor=_current_actor(),
                action="create",
                resource=f"family/{family.id}",
                after={"name": name, "timezone": timezone},
            )
        await self._commit()
        return family.id

    async def create_user(
        self,
        *,
        family_id: str,
        role: Role,
        display_name: str,
        plain_password: str,
        audit: AuditService | None = None,
    ) -> str:
        """创建家庭成员（密码经 ``PasswordHasher`` 哈希），返回用户 id（ULID）。

        家庭不存在 → ``NotFoundError``；同名成员已存在 → ``ConflictError``（409）。
        密码以 PBKDF2 哈希存储（§20：不得明文）。
        """
        family = await self._repo.get_family(family_id)
        if family is None:
            raise NotFoundError("Family not found", evidence={"family_id": family_id})
        existing = await self._repo.get_user_by_family(family_id, display_name)
        if existing is not None:
            raise ConflictError(
                "User already exists in family",
                evidence={"family_id": family_id, "display_name": display_name},
            )

        auth_hash = self._hasher.hash(plain_password)
        user = await self._repo.create_user(family_id, role, display_name, auth_hash)
        if audit is not None:
            await audit.append(
                actor=_current_actor(),
                action="create",
                resource=f"user/{user.id}",
                after={
                    "family_id": family_id,
                    "role": role.value,
                    "display_name": display_name,
                },
            )
        await self._commit()
        return user.id

    async def register_device(
        self,
        *,
        principal: Principal,
        kind: DeviceKind,
        fcm_token: str | None = None,
        meta: dict[str, Any] | None = None,
        audit: AuditService | None = None,
    ) -> str:
        """注册设备到 principal 所属家庭，返回设备 id（ULID）。

        权限（架构 §19）：``device:register`` 仅 Admin（P0）；deny → ``ForbiddenError``。
        ``fcm_token`` 存独立字段（§6.1 device 表），其余扩展信息存 ``meta`` jsonb。
        """
        self.authorize(principal, "device:register")
        if self._device_repo is None:
            raise RuntimeError("DeviceRepository not configured")
        device = await self._device_repo.create_device(
            family_id=principal.family_id,
            kind=kind,
            fcm_token=fcm_token,
            meta=meta,
        )
        if audit is not None:
            await audit.append(
                actor=principal.user_id,
                action="register",
                resource=f"device/{device.id}",
                after={
                    "family_id": principal.family_id,
                    "kind": kind.value,
                    "fcm_token": fcm_token,
                },
            )
        await self._commit()
        return device.id


def _current_actor() -> str:
    """从 logger contextvars 取当前操作人（user_id/device_id/system）。

    与 ``@audit`` 装饰器一致（§10.4）：无上下文则 ``system``。
    """
    from ...observability.logger import get_context  # 延迟导入避免循环依赖

    ctx = get_context()
    return ctx.get("user_id") or ctx.get("device_id") or "system"


__all__ = ["AuthService"]

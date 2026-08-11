# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""Auth 用例服务单元测试（APC-T007 测试要求：Unit RBAC allow/deny + 验收：可创建 family/user）。

验证 ``AuthService``：
    - authenticate：成功返回 Principal；家庭不存在 NotFoundError；用户不存在/密码错 AuthError。
    - issue_token / authenticate_token 往返：Principal 经 JWT 还原。
    - RBAC：can() allow/deny；authorize() deny → ForbiddenError（403）。
    - create_user：密码哈希存储（不存明文）；重复 → ConflictError；家庭不存在 → NotFoundError。
    - create_family：返回家庭 id。

用 ``FakeUserRepository`` 替身（不依赖 DB），符合架构 §5（Protocol + DI，测试注入替身）。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest

from server.app.auth.domain import (
    JwtService,
    PasswordHasher,
    Principal,
    Role,
)
from server.app.auth.service.auth_service import AuthService
from server.app.auth.service.jwt import Hs256JwtService
from server.app.auth.service.password import Pbkdf2PasswordHasher
from server.app.common.errors import AuthError, ConflictError, ForbiddenError, NotFoundError

# ---- 替身 ----


@dataclass
class FakeUser:
    id: str
    family_id: str
    role: str
    display_name: str
    auth_hash: str
    is_deleted: bool = False


@dataclass
class FakeFamily:
    id: str
    name: str
    timezone: str
    is_deleted: bool = False


class FakeUserRepository:
    """内存仓储替身（实现 ``domain.UserRepository``）。"""

    def __init__(self) -> None:
        self.users: dict[str, FakeUser] = {}
        self.families: dict[str, FakeFamily] = {}

    async def get_user(self, user_id: str) -> FakeUser | None:
        u = self.users.get(user_id)
        return u if u and not u.is_deleted else None

    async def get_user_by_family(self, family_id: str, display_name: str) -> FakeUser | None:
        for u in self.users.values():
            if u.family_id == family_id and u.display_name == display_name and not u.is_deleted:
                return u
        return None

    async def get_family(self, family_id: str) -> FakeFamily | None:
        f = self.families.get(family_id)
        return f if f and not f.is_deleted else None

    async def create_family(self, name: str, timezone: str) -> FakeFamily:
        from server.app.common.ids import new_id

        f = FakeFamily(id=new_id(), name=name, timezone=timezone)
        self.families[f.id] = f
        return f

    async def create_user(
        self, family_id: str, role: Role, display_name: str, auth_hash: str
    ) -> FakeUser:
        from server.app.common.ids import new_id

        u = FakeUser(
            id=new_id(),
            family_id=family_id,
            role=role.value,
            display_name=display_name,
            auth_hash=auth_hash,
        )
        self.users[u.id] = u
        return u


class FixedClock:
    """固定时钟替身（控制 iat/exp）。"""

    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


# ---- fixtures ----


@pytest.fixture
def repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def hasher() -> PasswordHasher:
    return Pbkdf2PasswordHasher(iterations=10_000)  # 测试用低迭代加速


@pytest.fixture
def jwt_svc() -> JwtService:
    return Hs256JwtService(secret="test-secret", access_ttl_seconds=3600)


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(datetime(2026, 8, 11, 12, 0, tzinfo=UTC))


@pytest.fixture
def auth_service(
    repo: FakeUserRepository,
    hasher: PasswordHasher,
    jwt_svc: JwtService,
    clock: FixedClock,
) -> AuthService:
    return AuthService(
        repository=repo,
        password_hasher=hasher,
        jwt_service=jwt_svc,
        clock=clock,
        access_ttl_seconds=3600,
    )


def _seed_family_with_admin(
    repo: FakeUserRepository, hasher: PasswordHasher, *, password: str = "admin-pass"
) -> tuple[str, str]:
    """种子一个家庭 + Admin 成员，返回 (family_id, user_id)。"""
    import asyncio

    async def _seed() -> tuple[str, str]:
        f = await repo.create_family("张家", "Asia/Shanghai")
        u = await repo.create_user(f.id, Role.ADMIN, "Dad", hasher.hash(password))
        return f.id, u.id

    return asyncio.run(_seed())


# ---- authenticate ----


def test_authenticate_success_returns_principal(
    auth_service: AuthService, repo: FakeUserRepository, hasher: PasswordHasher
):
    family_id, _ = _seed_family_with_admin(repo, hasher, password="admin-pass")
    principal = _run(
        auth_service.authenticate(
            family_id=family_id, display_name="Dad", plain_password="admin-pass"
        )
    )
    assert principal.family_id == family_id
    assert principal.role == Role.ADMIN
    assert principal.user_id  # ULID
    assert principal.device_id is None  # 未绑定设备


def test_authenticate_with_device_id(
    auth_service: AuthService, repo: FakeUserRepository, hasher: PasswordHasher
):
    family_id, _ = _seed_family_with_admin(repo, hasher)
    principal = _run(
        auth_service.authenticate(
            family_id=family_id,
            display_name="Dad",
            plain_password="admin-pass",
            device_id="01JZDEVICE",
        )
    )
    assert principal.device_id == "01JZDEVICE"


def test_authenticate_family_not_found_raises_not_found(auth_service: AuthService):
    with pytest.raises(NotFoundError):
        _run(
            auth_service.authenticate(
                family_id="nonexistent", display_name="Dad", plain_password="x"
            )
        )


def test_authenticate_user_not_found_raises_auth_error(
    auth_service: AuthService, repo: FakeUserRepository, hasher: PasswordHasher
):
    family_id, _ = _seed_family_with_admin(repo, hasher)
    with pytest.raises(AuthError):
        _run(
            auth_service.authenticate(family_id=family_id, display_name="Ghost", plain_password="x")
        )


def test_authenticate_wrong_password_raises_auth_error(
    auth_service: AuthService, repo: FakeUserRepository, hasher: PasswordHasher
):
    """密码错 → AuthError（与用户不存在统一，防用户枚举，§20）。"""
    family_id, _ = _seed_family_with_admin(repo, hasher, password="correct")
    with pytest.raises(AuthError):
        _run(
            auth_service.authenticate(
                family_id=family_id, display_name="Dad", plain_password="wrong"
            )
        )


# ---- issue_token / authenticate_token ----


def test_issue_and_authenticate_token_roundtrip(auth_service: AuthService):
    principal = Principal(
        user_id="01JZUSER", family_id="01JZFAM", role=Role.ADMIN, device_id="01JZDEV"
    )
    token, claims = auth_service.issue_token(principal)
    assert token.count(".") == 2
    assert claims.role == Role.ADMIN

    restored = auth_service.authenticate_token(token)
    assert restored == principal


def test_authenticate_token_invalid_raises_auth_error(auth_service: AuthService):
    with pytest.raises(AuthError):
        auth_service.authenticate_token("garbage.token.here")


# ---- RBAC ----


def test_can_admin_allows_all_p0_actions():
    admin = Principal(user_id="u", family_id="f", role=Role.ADMIN)
    for action in ("event:write", "event:read", "alert:ack", "rule:configure", "export"):
        assert AuthService.can(admin, action), f"Admin should permit {action}"


def test_can_viewer_denies_write():
    viewer = Principal(user_id="u", family_id="f", role=Role.VIEWER)
    assert AuthService.can(viewer, "event:read") is True
    assert AuthService.can(viewer, "media:read") is True
    # Viewer 不可写（§19：只读摘要、相册）。
    assert AuthService.can(viewer, "event:write") is False
    assert AuthService.can(viewer, "rule:configure") is False


def test_can_caregiver_denies_rule_config():
    """Caregiver 不可改医疗/系统规则（§19）。"""
    caregiver = Principal(user_id="u", family_id="f", role=Role.CAREGIVER)
    assert AuthService.can(caregiver, "event:write") is True
    assert AuthService.can(caregiver, "rule:configure") is False
    assert AuthService.can(caregiver, "rule:activate") is False


def test_can_system_allows_event_write():
    system = Principal(user_id="system", family_id="f", role=Role.SYSTEM)
    assert AuthService.can(system, "event:write") is True
    assert AuthService.can(system, "rule:configure") is False


def test_can_unknown_action_denied_by_default():
    """未列出的动作默认 deny（最小权限）。"""
    admin = Principal(user_id="u", family_id="f", role=Role.ADMIN)
    assert AuthService.can(admin, "nonexistent:action") is False


def test_authorize_admin_allow_does_not_raise():
    admin = Principal(user_id="u", family_id="f", role=Role.ADMIN)
    AuthService.authorize(admin, "event:write")  # 不抛


def test_authorize_viewer_denied_raises_forbidden():
    viewer = Principal(user_id="u", family_id="f", role=Role.VIEWER)
    with pytest.raises(ForbiddenError) as exc_info:
        AuthService.authorize(viewer, "event:write")
    assert exc_info.value.http_status == 403
    assert exc_info.value.evidence is not None
    assert exc_info.value.evidence["role"] == "viewer"
    assert exc_info.value.evidence["action"] == "event:write"


def test_authorize_caregiver_rule_config_denied():
    """非授权角色访问受限方法被拒（T007 验收标准）。"""
    caregiver = Principal(user_id="u", family_id="f", role=Role.CAREGIVER)
    with pytest.raises(ForbiddenError):
        AuthService.authorize(caregiver, "rule:configure")


# ---- create_user / create_family ----


def test_create_user_hashes_password_not_stored_plain(
    auth_service: AuthService, repo: FakeUserRepository, hasher: PasswordHasher
):
    """密码经哈希存储，不存明文（§20）。"""
    family_id, _ = _seed_family_with_admin(repo, hasher)
    user_id = _run(
        auth_service.create_user(
            family_id=family_id,
            role=Role.CAREGIVER,
            display_name="Nanny",
            plain_password="nanny-secret",
        )
    )
    user = repo.users[user_id]
    assert user.auth_hash != "nanny-secret"
    assert "nanny-secret" not in user.auth_hash
    # 存储的哈希可被 hasher 校验。
    assert hasher.verify("nanny-secret", user.auth_hash) is True
    assert user.role == "caregiver"


def test_create_user_duplicate_raises_conflict(
    auth_service: AuthService, repo: FakeUserRepository, hasher: PasswordHasher
):
    family_id, _ = _seed_family_with_admin(repo, hasher)
    _run(
        auth_service.create_user(
            family_id=family_id, role=Role.VIEWER, display_name="Mom", plain_password="p"
        )
    )
    with pytest.raises(ConflictError):
        _run(
            auth_service.create_user(
                family_id=family_id, role=Role.VIEWER, display_name="Mom", plain_password="p"
            )
        )


def test_create_user_family_not_found_raises_not_found(auth_service: AuthService):
    with pytest.raises(NotFoundError):
        _run(
            auth_service.create_user(
                family_id="nonexistent",
                role=Role.ADMIN,
                display_name="Dad",
                plain_password="p",
            )
        )


def test_create_family_returns_id(auth_service: AuthService, repo: FakeUserRepository):
    family_id = _run(auth_service.create_family(name="李家", timezone="Asia/Shanghai"))
    assert family_id in repo.families
    assert repo.families[family_id].name == "李家"
    assert repo.families[family_id].timezone == "Asia/Shanghai"


def test_create_user_without_audit_still_works(
    auth_service: AuthService, repo: FakeUserRepository, hasher: PasswordHasher
):
    """T007 阶段无 API 层：audit=None 时 create_user 正常工作（T008 gateway 注入启用留痕）。"""
    family_id, _ = _seed_family_with_admin(repo, hasher)
    user_id = _run(
        auth_service.create_user(
            family_id=family_id,
            role=Role.VIEWER,
            display_name="Aunt",
            plain_password="p",
            audit=None,
        )
    )
    assert user_id


# ---- helpers ----


def _run(coro: Any) -> Any:
    """同步执行 async 调用（测试用，单事件循环）。"""
    import asyncio

    return asyncio.run(coro)

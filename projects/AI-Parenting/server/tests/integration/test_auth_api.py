# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""Auth API 集成测试（APC-T008，需 DB）。

两类测试：
    1. HTTP 流程（login/refresh/me/forbidden）：用 dependency_overrides 注入内存仓储替身，
       避免与 TestClient event loop 跨循环的 engine 死连接问题（test_audit 注释）。
    2. DB 写入（register-device、seed_family）：纯 DB 测试（asyncio.run + reset_db），
       不混 TestClient，与 test_audit 同模式。

标记 integration（需真实 PG）；通过 PARENTING_DATABASE__URL 指向 AI_parenting_dev。
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from server.app.auth.domain import Role
from server.app.auth.infra.repository import SqlAlchemyUserRepository
from server.app.auth.service.auth_service import AuthService
from server.app.auth.service.jwt import Hs256JwtService
from server.app.auth.service.password import Pbkdf2PasswordHasher
from server.app.common.clock import SystemClock
from server.app.db import get_session_factory
from server.app.models.core import Device
from server.app.settings import get_settings

pytestmark = pytest.mark.integration


# ---- 内存替身（HTTP 流程测试用）----


class _FakeUser:
    def __init__(self, user_id: str, family_id: str, role: str, display_name: str, auth_hash: str):
        self.id = user_id
        self.family_id = family_id
        self.role = role
        self.display_name = display_name
        self.auth_hash = auth_hash
        self.is_deleted = False


class _FakeFamily:
    def __init__(self, family_id: str):
        self.id = family_id
        self.name = "fake"
        self.timezone = "Asia/Shanghai"
        self.is_deleted = False


class _FakeUserRepository:
    """内存仓储替身（实现 domain.UserRepository + DeviceRepository）。"""

    def __init__(self) -> None:
        self._hasher = Pbkdf2PasswordHasher(iterations=10_000)
        self.family_id = "01JZFAKEFAMILY00000001"
        self.admin_id = "01JZFAKEADMIN0000000001"
        self.viewer_id = "01JZFAKEVIEWER000000001"
        self.users = {
            self.admin_id: _FakeUser(
                self.admin_id, self.family_id, "admin", "Dad", self._hasher.hash("admin-pass")
            ),
            self.viewer_id: _FakeUser(
                self.viewer_id, self.family_id, "viewer", "Aunt", self._hasher.hash("viewer-pass")
            ),
        }
        self.families = {self.family_id: _FakeFamily(self.family_id)}
        self.devices: dict[str, dict] = {}

    async def get_user(self, user_id: str):
        return self.users.get(user_id)

    async def get_user_by_family(self, family_id: str, display_name: str):
        for u in self.users.values():
            if u.family_id == family_id and u.display_name == display_name:
                return u
        return None

    async def get_family(self, family_id: str):
        return self.families.get(family_id)

    async def create_family(self, name: str, timezone: str):
        return _FakeFamily("01JZNEWFAMILY0000000001")

    async def create_user(self, family_id: str, role: Role, display_name: str, auth_hash: str):
        return _FakeUser("01JZNEWUSER00000000001", family_id, role.value, display_name, auth_hash)

    async def create_device(self, family_id: str, kind, fcm_token, meta):
        from server.app.common.ids import new_id

        device_id = new_id()
        self.devices[device_id] = {
            "family_id": family_id,
            "kind": kind.value,
            "fcm_token": fcm_token,
            "meta": meta,
        }
        return _FakeDevice(device_id, family_id, kind.value, fcm_token, meta)


class _FakeDevice:
    def __init__(self, device_id, family_id, kind, fcm_token, meta):
        self.id = device_id
        self.family_id = family_id
        self.kind = kind
        self.fcm_token = fcm_token
        self.meta = meta
        self.is_deleted = False


def _make_fake_auth_service() -> AuthService:
    """构造用内存替身的 AuthService（无 session，mutating 不 commit）。"""
    repo = _FakeUserRepository()
    settings = get_settings()
    return AuthService(
        repository=repo,
        password_hasher=Pbkdf2PasswordHasher(iterations=10_000),
        jwt_service=Hs256JwtService(
            secret=settings.auth.jwt_secret, access_ttl_seconds=settings.auth.access_ttl_seconds
        ),
        clock=SystemClock(),
        access_ttl_seconds=settings.auth.access_ttl_seconds,
        device_repository=repo,  # 同一替身兼作 DeviceRepository
    )


# ---- HTTP 流程测试（dependency_overrides 注入替身）----


@pytest.fixture
def client_with_fake_auth(client: TestClient) -> Iterator[TestClient]:
    """注入内存替身 AuthService 的 TestClient（避免跨 loop DB 问题）。"""
    fake_svc = _make_fake_auth_service()

    async def _override_auth_service():
        yield fake_svc

    from typing import cast

    from fastapi import FastAPI

    from server.app.di import get_auth_service_dep

    app = cast(FastAPI, client.app)
    app.dependency_overrides[get_auth_service_dep] = _override_auth_service
    yield client
    app.dependency_overrides.clear()


def test_login_token_protected_endpoint(client_with_fake_auth: TestClient):
    """login → token → /me 端到端（T008 验收：login → token → protected endpoint）。"""
    resp = client_with_fake_auth.post(
        "/api/v1/auth/login",
        json={
            "family_id": "01JZFAKEFAMILY00000001",
            "display_name": "Dad",
            "password": "admin-pass",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["token_type"] == "Bearer"
    assert body["role"] == "admin"
    token = body["access_token"]

    me = client_with_fake_auth.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200, me.text
    assert me.json()["role"] == "admin"


def test_login_wrong_password_returns_401(client_with_fake_auth: TestClient):
    """错误密码 → 401。"""
    resp = client_with_fake_auth.post(
        "/api/v1/auth/login",
        json={
            "family_id": "01JZFAKEFAMILY00000001",
            "display_name": "Dad",
            "password": "wrong",
        },
    )
    assert resp.status_code == 401


def test_protected_endpoint_without_token_returns_401(client: TestClient):
    """无 Authorization header → 401（不需 DB，用默认 client）。"""
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 401


def test_protected_endpoint_with_invalid_token_returns_401(client: TestClient):
    """非法 token → 401。"""
    me = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not.a.valid.token"})
    assert me.status_code == 401


def test_refresh_issues_new_token(client_with_fake_auth: TestClient):
    """refresh → 新 token。"""
    token = client_with_fake_auth.post(
        "/api/v1/auth/login",
        json={
            "family_id": "01JZFAKEFAMILY00000001",
            "display_name": "Dad",
            "password": "admin-pass",
        },
    ).json()["access_token"]
    resp = client_with_fake_auth.post(
        "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, resp.text
    new_token = resp.json()["access_token"]
    assert new_token != token


def test_register_device_admin_returns_201(client_with_fake_auth: TestClient):
    """Admin 注册设备 → 201（替身内存）。"""
    token = client_with_fake_auth.post(
        "/api/v1/auth/login",
        json={
            "family_id": "01JZFAKEFAMILY00000001",
            "display_name": "Dad",
            "password": "admin-pass",
        },
    ).json()["access_token"]
    resp = client_with_fake_auth.post(
        "/api/v1/auth/register-device",
        headers={"Authorization": f"Bearer {token}"},
        json={"kind": "phone", "fcm_token": "token-abc", "meta": {"os": "android"}},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["kind"] == "phone"


def test_register_device_viewer_forbidden(client_with_fake_auth: TestClient):
    """Viewer 注册设备 → 403（§19：device:register 仅 Admin）。"""
    token = client_with_fake_auth.post(
        "/api/v1/auth/login",
        json={
            "family_id": "01JZFAKEFAMILY00000001",
            "display_name": "Aunt",
            "password": "viewer-pass",
        },
    ).json()["access_token"]
    resp = client_with_fake_auth.post(
        "/api/v1/auth/register-device",
        headers={"Authorization": f"Bearer {token}"},
        json={"kind": "phone"},
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "PARENTING.FORBIDDEN"


# ---- DB 写入测试（纯 DB，不混 TestClient，与 test_audit 同模式）----


@pytest.fixture(autouse=True)
def _reset_db():
    """同步重置进程级 engine 缓存（避免跨测试死连接）。

    HTTP 流程测试用 fake 替身不碰 DB，但 reset 无害；纯 DB 测试依赖它确保独立 engine。
    """
    from server.app import db as db_module

    db_module.reset_db()
    yield
    db_module.reset_db()


def _make_svc(session, *, device_repo=None) -> AuthService:
    """构造 AuthService（测试用低迭代）。"""
    settings = get_settings()
    from server.app.auth.infra.repository import SqlAlchemyDeviceRepository

    return AuthService(
        repository=SqlAlchemyUserRepository(session),
        password_hasher=Pbkdf2PasswordHasher(iterations=10_000),
        jwt_service=Hs256JwtService(
            secret=settings.auth.jwt_secret,
            access_ttl_seconds=settings.auth.access_ttl_seconds,
        ),
        clock=SystemClock(),
        access_ttl_seconds=settings.auth.access_ttl_seconds,
        device_repository=device_repo or SqlAlchemyDeviceRepository(session),
        session=session,
    )


def test_register_device_writes_to_db():
    """register_device 写入 device 表（T008 验收：设备注册写入 DB）—— 纯 DB 验证，单 asyncio.run。"""

    async def run() -> dict:
        from server.app.auth.domain import DeviceKind, Principal

        settings = get_settings()
        factory = get_session_factory(settings)
        async with factory() as session:
            svc = _make_svc(session)
            family_id = await svc.create_family(name="DB测试家", timezone="Asia/Shanghai")
            await svc.create_user(
                family_id=family_id,
                role=Role.ADMIN,
                display_name="Dad",
                plain_password="admin-pass",
            )
            principal = Principal(
                user_id="01JZUSER", family_id=family_id, role=Role.ADMIN, device_id=None
            )
            device_id = await svc.register_device(
                principal=principal, kind=DeviceKind.PHONE, fcm_token="fcm-xyz", meta={"os": "ios"}
            )
            # 读回验证。
            row = (
                await session.execute(
                    select(
                        Device.id, Device.family_id, Device.kind, Device.fcm_token, Device.meta
                    ).where(Device.id == device_id)
                )
            ).one()
        return dict(row._mapping)

    row = asyncio.run(run())
    assert row["kind"] == "phone"
    assert row["fcm_token"] == "fcm-xyz"
    assert row["meta"] == {"os": "ios"}


def test_seed_family_script_creates_family_users_baby():
    """seed_family 脚本端到端：创建家庭、父母 Admin、baby，幂等。"""
    from server.app import db as db_module
    from server.scripts.seed_family import seed

    result1 = asyncio.run(seed())
    assert result1["family_id"]
    assert result1["dad_id"]
    assert result1["mom_id"]
    assert result1["baby_id"]
    # 幂等：重置 engine（前一次 asyncio.run 的 loop 已关闭）后再跑。
    db_module.reset_db()
    result2 = asyncio.run(seed())
    assert result2 == result1

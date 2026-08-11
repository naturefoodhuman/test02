# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""Auth 仓储与服务集成测试（APC-T007，需 DB）。

连 AI_parenting_dev 库验证：
    - SqlAlchemyUserRepository.create_family/create_user 端到端写入 family/user 表。
    - AuthService.create_user 密码经 PBKDF2 哈希存储（不存明文，§20）。
    - AuthService.authenticate 端到端：正确密码返回 Principal；错误密码 AuthError。
    - AuthService.issue_token / authenticate_token 往返（HS256 JWT）。

标记 integration（需真实 PG）；通过 PARENTING_DATABASE__URL 指向 AI_parenting_dev。
每个测试用单一 asyncio.run（避免跨事件循环的 engine 死连接问题，与 test_audit 一致）。
"""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import select

from server.app import db as db_module
from server.app.auth.domain import Role
from server.app.auth.infra.repository import SqlAlchemyUserRepository
from server.app.auth.service.auth_service import AuthService
from server.app.auth.service.jwt import Hs256JwtService
from server.app.auth.service.password import Pbkdf2PasswordHasher
from server.app.common.clock import SystemClock
from server.app.common.errors import AuthError, NotFoundError
from server.app.db import get_session_factory
from server.app.models.core import User

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _reset_db():
    """同步重置进程级 engine 缓存（避免跨测试死连接）。"""
    db_module.reset_db()
    yield
    db_module.reset_db()


def _make_service(session) -> AuthService:
    return AuthService(
        repository=SqlAlchemyUserRepository(session),
        password_hasher=Pbkdf2PasswordHasher(iterations=10_000),  # 测试用低迭代加速
        jwt_service=Hs256JwtService(secret="integration-test-secret", access_ttl_seconds=3600),
        clock=SystemClock(),
        access_ttl_seconds=3600,
    )


def test_create_family_and_user_persists_with_hashed_password():
    """端到端：创建家庭 + Admin 用户，密码哈希存储，authenticate 成功。"""

    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as session:
            svc = _make_service(session)
            family_id = await svc.create_family(name="集成测试家", timezone="Asia/Shanghai")
            user_id = await svc.create_user(
                family_id=family_id,
                role=Role.ADMIN,
                display_name="Dad",
                plain_password="integration-pass",
            )
            await session.commit()
            # 读回验证：auth_hash 非明文。
            row = (
                await session.execute(
                    select(
                        User.id, User.family_id, User.role, User.display_name, User.auth_hash
                    ).where(User.id == user_id)
                )
            ).one()
        return dict(row._mapping)

    row = asyncio.run(run())
    assert row["role"] == "admin"
    assert row["display_name"] == "Dad"
    assert row["auth_hash"] != "integration-pass"
    assert "integration-pass" not in row["auth_hash"]
    assert row["auth_hash"].startswith("pbkdf2_sha256$")


def test_authenticate_end_to_end_success_and_failure():
    """端到端：正确密码返回 Principal；错误密码 AuthError；家庭不存在 NotFoundError。"""

    async def run() -> tuple[str, str]:
        factory = get_session_factory()
        async with factory() as session:
            svc = _make_service(session)
            family_id = await svc.create_family(name="鉴权测试家", timezone="Asia/Shanghai")
            await svc.create_user(
                family_id=family_id,
                role=Role.ADMIN,
                display_name="Mom",
                plain_password="correct-pass",
            )
            await session.commit()
        # 新 session 鉴权（模拟独立请求）。
        async with factory() as session:
            svc = _make_service(session)
            principal = await svc.authenticate(
                family_id=family_id, display_name="Mom", plain_password="correct-pass"
            )
            assert principal.role == Role.ADMIN
            assert principal.family_id == family_id
            # 错误密码。
            with pytest.raises(AuthError):
                await svc.authenticate(
                    family_id=family_id, display_name="Mom", plain_password="wrong-pass"
                )
            # 家庭不存在。
            with pytest.raises(NotFoundError):
                await svc.authenticate(
                    family_id="01JZNONEXIST", display_name="Mom", plain_password="x"
                )
        return family_id, principal.user_id

    asyncio.run(run())


def test_issue_and_authenticate_token_end_to_end():
    """端到端：authenticate → issue_token → authenticate_token 往返。"""

    async def run() -> None:
        factory = get_session_factory()
        async with factory() as session:
            svc = _make_service(session)
            family_id = await svc.create_family(name="JWT测试家", timezone="Asia/Shanghai")
            await svc.create_user(
                family_id=family_id,
                role=Role.ADMIN,
                display_name="Dad",
                plain_password="jwt-pass",
            )
            await session.commit()
        async with factory() as session:
            svc = _make_service(session)
            principal = await svc.authenticate(
                family_id=family_id, display_name="Dad", plain_password="jwt-pass"
            )
            token, _claims = svc.issue_token(principal)
            restored = svc.authenticate_token(token)
            assert restored.user_id == principal.user_id
            assert restored.family_id == family_id
            assert restored.role == Role.ADMIN

    asyncio.run(run())

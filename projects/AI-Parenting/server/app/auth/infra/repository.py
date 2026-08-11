# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/auth/infra/repository.py —— Auth 仓储实现（家庭/用户 CRUD）。
# 依据：ENGINEERING_DESIGN §5.2（Repository Protocol）、§6.1（family/user 表）；
#       ARCHITECTURE_FINAL §6/§7（PostgreSQL 权威源）；TASK_BACKLOG APC-T007。
# 设计：基于 AsyncSession 的请求作用域仓储（架构 §5.2：生命周期请求作用域，事务边界在 service）。
#       ULID PK 应用层生成（ULIDPrimaryKey 不自动生成）；created_at/updated_at 走 ORM default。
#       软删除过滤：查询默认排除 is_deleted（partial unique index 语义对齐）。
# 边界：只做数据访问，不含业务规则（角色/权限判定在 service）；异常由 service 层映射。

"""Auth 仓储实现（家庭/用户 CRUD）。

架构（ENGINEERING_DESIGN §5.2）：``Repository`` 请求作用域，事务边界在 service 层。
本模块实现 ``domain.UserRepository`` 协议，基于 ``AsyncSession``，仅做数据访问；
业务规则（角色校验、权限判定、哈希）在 ``auth.service``。

表结构 SSOT：``ENGINEERING_DESIGN §6.1`` ——
- ``family``：id, name, timezone, created_at, updated_at, is_deleted。
- ``user``：id, family_id FK, role, display_name, auth_hash, created_at, updated_at, is_deleted。

软删除：查询默认 ``is_deleted = false``（与 partial unique index 语义一致）。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...common.ids import new_id
from ...models.core import Device, Family, User
from ..domain import DeviceKind, Role


class SqlAlchemyUserRepository:
    """基于 ``AsyncSession`` 的家庭/用户仓储（实现 ``domain.UserRepository``）。

    生命周期：请求作用域（FastAPI ``Depends`` 注入 session）；事务边界在 service 层
    （service 决定 commit/rollback）。本仓储只 execute/flush，不 commit。

    ``domain.UserRepository`` 协议声明返回 ``object`` 以解耦领域与 ORM（架构 §5：
    Protocol 不绑实现）；本实现返回具体 ``Family`` / ``User`` ORM 实例，调用方按需读取属性。
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user(self, user_id: str) -> User | None:
        """按 id 取未删除的用户。"""
        stmt = select(User).where(User.id == user_id, User.is_deleted.is_(False))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_family(self, family_id: str, display_name: str) -> User | None:
        """按家庭 + 显示名取未删除用户（登录场景：家庭内按名定位成员）。"""
        stmt = select(User).where(
            User.family_id == family_id,
            User.display_name == display_name,
            User.is_deleted.is_(False),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_family(self, family_id: str) -> Family | None:
        """按 id 取未删除的家庭。"""
        stmt = select(Family).where(Family.id == family_id, Family.is_deleted.is_(False))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_family(self, name: str, timezone: str) -> Family:
        """创建家庭；flush 以取得 server-default（created_at 等），不 commit。

        返回的 ``Family`` 实例 ``id`` 在 flush 后可用（应用层已赋 ULID）。
        """
        family = Family(id=new_id(), name=name, timezone=timezone)
        self._session.add(family)
        await self._session.flush()
        return family

    async def create_user(
        self, family_id: str, role: Role, display_name: str, auth_hash: str
    ) -> User:
        """创建家庭成员（``auth_hash`` 已由 service 层哈希）；flush 不 commit。"""
        user = User(
            id=new_id(),
            family_id=family_id,
            role=role.value,
            display_name=display_name,
            auth_hash=auth_hash,
        )
        self._session.add(user)
        await self._session.flush()
        return user


__all__ = ["SqlAlchemyDeviceRepository", "SqlAlchemyUserRepository"]


class SqlAlchemyDeviceRepository:
    """基于 ``AsyncSession`` 的设备仓储（实现 ``domain.DeviceRepository``）。

    生命周期：请求作用域；flush 不 commit（事务边界在 service）。
    ``fcm_token`` 存独立字段（§6.1 device 表），其余扩展信息存 ``meta`` jsonb。
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_device(
        self,
        family_id: str,
        kind: DeviceKind,
        fcm_token: str | None,
        meta: dict[str, Any] | None,
    ) -> Device:
        """注册设备；flush 不 commit。"""
        device = Device(
            id=new_id(),
            family_id=family_id,
            kind=kind.value,
            fcm_token=fcm_token,
            meta=meta,
        )
        self._session.add(device)
        await self._session.flush()
        return device

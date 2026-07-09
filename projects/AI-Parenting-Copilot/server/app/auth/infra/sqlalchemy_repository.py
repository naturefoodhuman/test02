# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 15:20:00


"""SQLAlchemy AuthRepository implementation.

This adapter is intentionally thin and mirrors the in-memory repository contract.
Live DB integration tests run during Mac/PostgreSQL validation.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.auth.domain.models import Device, DeviceKind, Family, Role, User
from server.app.models import Baby as ORMBaby
from server.app.models import Device as ORMDevice
from server.app.models import Family as ORMFamily
from server.app.models import User as ORMUser


class SQLAlchemyAuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_family(self, family: Family) -> Family:
        self.session.add(ORMFamily(id=family.id, name=family.name, timezone=family.timezone))
        await self.session.flush()
        return family

    async def add_user(self, user: User) -> User:
        self.session.add(
            ORMUser(
                id=user.id,
                family_id=user.family_id,
                role=user.role.value,
                display_name=user.display_name,
                auth_hash=user.auth_hash,
                is_deleted=user.is_deleted,
            )
        )
        await self.session.flush()
        return user

    async def add_device(self, device: Device) -> Device:
        self.session.add(
            ORMDevice(
                id=device.id,
                family_id=device.family_id,
                user_id=device.user_id,
                kind=device.kind.value,
                name=device.name,
                fcm_token=device.fcm_token,
                meta=device.meta,
            )
        )
        await self.session.flush()
        return device

    async def get_user(self, user_id: str) -> User | None:
        row = await self.session.scalar(select(ORMUser).where(ORMUser.id == user_id))
        return self._to_user(row) if row is not None else None

    async def get_user_by_display_name(self, family_id: str, display_name: str) -> User | None:
        row = await self.session.scalar(
            select(ORMUser).where(
                ORMUser.family_id == family_id,
                ORMUser.display_name == display_name,
                ORMUser.is_deleted.is_(False) if False else ORMUser.is_deleted.is_(False),
            )
        )
        return self._to_user(row) if row is not None else None

    async def list_family_users(self, family_id: str) -> list[User]:
        result = await self.session.scalars(select(ORMUser).where(ORMUser.family_id == family_id))
        return [self._to_user(row) for row in result]

    async def add_baby(self, *, family_id: str, baby_id: str, name: str) -> None:
        self.session.add(ORMBaby(id=baby_id, family_id=family_id, name=name))
        await self.session.flush()

    @staticmethod
    def _to_user(row: ORMUser) -> User:
        return User(
            id=row.id,
            family_id=row.family_id,
            display_name=row.display_name,
            role=Role(row.role),
            auth_hash=row.auth_hash,
            is_deleted=row.is_deleted,
        )

    @staticmethod
    def _to_device(row: ORMDevice) -> Device:
        return Device(
            id=row.id,
            family_id=row.family_id,
            user_id=row.user_id,
            kind=DeviceKind(row.kind),
            name=row.name,
            fcm_token=row.fcm_token,
            meta=row.meta,
        )

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 01:15:00


"""Auth repository protocols and in-memory adapter."""

from __future__ import annotations

from typing import Protocol

from server.app.auth.domain.models import Device, Family, User


class AuthRepository(Protocol):
    async def add_family(self, family: Family) -> Family: ...
    async def add_user(self, user: User) -> User: ...
    async def add_device(self, device: Device) -> Device: ...
    async def get_user(self, user_id: str) -> User | None: ...
    async def get_user_by_display_name(self, family_id: str, display_name: str) -> User | None: ...
    async def list_family_users(self, family_id: str) -> list[User]: ...


class InMemoryAuthRepository:
    """Deterministic auth repository for tests/dev mode until DB repository lands."""

    def __init__(self) -> None:
        self.families: dict[str, Family] = {}
        self.users: dict[str, User] = {}
        self.devices: dict[str, Device] = {}

    async def add_family(self, family: Family) -> Family:
        self.families[family.id] = family
        return family

    async def add_user(self, user: User) -> User:
        self.users[user.id] = user
        return user

    async def add_device(self, device: Device) -> Device:
        self.devices[device.id] = device
        return device

    async def get_user(self, user_id: str) -> User | None:
        return self.users.get(user_id)

    async def get_user_by_display_name(self, family_id: str, display_name: str) -> User | None:
        for user in self.users.values():
            if (
                user.family_id == family_id
                and user.display_name == display_name
                and not user.is_deleted
            ):
                return user
        return None

    async def list_family_users(self, family_id: str) -> list[User]:
        return [user for user in self.users.values() if user.family_id == family_id]

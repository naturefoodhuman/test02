# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 01:15:00


"""Auth/RBAC domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from server.app.common.clock import utc_now
from server.app.common.ids import new_ulid


class Role(StrEnum):
    """Project roles from architecture §19."""

    ADMIN = "Admin"
    CAREGIVER = "Caregiver"
    VIEWER = "Viewer"
    SYSTEM = "System"


class DeviceKind(StrEnum):
    """Supported device kinds."""

    PHONE = "phone"
    CAMERA = "camera"
    MMWAVE = "mmwave"
    MAC = "mac"


@dataclass(slots=True)
class Family:
    name: str
    timezone: str = "Asia/Shanghai"
    id: str = field(default_factory=new_ulid)


@dataclass(slots=True)
class User:
    family_id: str
    display_name: str
    role: Role
    auth_hash: str | None = None
    id: str = field(default_factory=new_ulid)
    is_deleted: bool = False


@dataclass(slots=True)
class Device:
    family_id: str
    kind: DeviceKind
    user_id: str | None = None
    name: str | None = None
    fcm_token: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=new_ulid)
    last_seen_at_iso: str = field(default_factory=lambda: utc_now().isoformat())


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: str
    family_id: str
    role: Role
    device_id: str | None = None

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

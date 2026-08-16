# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/auth/domain.py —— Auth/RBAC 领域模型与协议（Protocol）。
# 依据：ENGINEERING_DESIGN §2（M02 auth）、§5（核心抽象 Protocol+DI）、§9.1（异常层次）；
#       ARCHITECTURE_FINAL §19（权限体系）、§20（安全体系）；TASK_BACKLOG APC-T007。
# 设计：领域层纯数据契约 + Protocol，不感知 HTTP/DB（架构 §5：Protocol + Pydantic 模型）。
#       Role 枚举对齐架构 §19（Admin/Caregiver/Viewer/System）；P0 仅 Admin 完整权限，
#       Caregiver/Viewer 预留权限表（V2 启用，§26.1）。
#       Principal 为鉴权产物（gateway 依赖注入），含 user_id/family_id/role/device_id（JWT claims SSOT）。
# 边界：domain 不含实现（哈希/JWT/DB 访问在 service/infra）；异常复用 common/errors.AuthError。

"""Auth/RBAC 领域模型与协议。

架构（ENGINEERING_DESIGN §5）：所有抽象以 ``Protocol`` + ``Pydantic`` 模型实现，测试可注入替身。
本模块定义角色、Principal、TokenClaims、权限表与各服务/仓储协议；不含实现细节
（哈希/JWT 编解码在 ``service``，DB 访问在 ``infra/repository``）。

角色与权限（ARCHITECTURE_FINAL §19）：
    - Admin（父亲/母亲）：记录、查看、确认告警、配置规则 —— P0 完整权限。
    - Caregiver：记录、查看部分状态；不可改医疗/系统规则；不可查看医疗建议 —— V2。
    - Viewer：只读摘要、相册 —— V2。
    - System：自动写入设备/分析/派生/告警事件 —— P0。

JWT claims SSOT（TASK_BACKLOG APC-T007）：``user_id`` / ``family_id`` / ``role`` / ``device_id``。
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class Role(StrEnum):
    """家庭成员角色（架构 §19）。

    ``StrEnum``：与 ORM ``user.role``（``String(32)``）直接互转，避免额外映射层。
    """

    ADMIN = "admin"
    CAREGIVER = "caregiver"
    VIEWER = "viewer"
    SYSTEM = "system"


# ---- 权限表（架构 §19 / §26.1 阶段路线）----
# P0：Admin 完整权限；System 自动写入派生/告警事件。
# Caregiver/Viewer 预留权限表，V2 启用（§26.1）；P0 阶段对受限方法返回 deny。
#
# 权限粒度：动作级（action），资源级校验在 service 层按需扩展（如医疗建议对
# Caregiver/Viewer 不可见，§19）。本表为 allow-list，未列出的动作默认 deny（最小权限）。
_PERMISSIONS: dict[Role, frozenset[str]] = {
    Role.ADMIN: frozenset(
        {
            "event:write",  # 记录
            "event:read",  # 查看
            "state:read",  # 派生状态查看（APC-T016）
            "alert:ack",  # 确认告警
            "rule:configure",  # 配置医疗/系统规则
            "rule:activate",  # 激活规则版本
            "family:manage",  # 家庭/用户管理
            "device:register",  # 设备注册
            "media:read",  # 相册
            "export",  # 导出
        }
    ),
    Role.SYSTEM: frozenset(
        {
            "event:write",  # 自动写入设备/分析/派生/告警事件
            "event:read",
        }
    ),
    # V2 预留：Caregiver/Viewer 权限表在 §26.1 V2 阶段填充；P0 阶段 deny 受限方法。
    Role.CAREGIVER: frozenset({"event:write", "event:read", "state:read"}),
    Role.VIEWER: frozenset({"event:read", "media:read", "state:read"}),
}


def permissions_for(role: Role) -> frozenset[str]:
    """返回角色拥有的权限集合（不可变）。

    未在 ``_PERMISSIONS`` 中显式列出的角色返回空集（最小权限，默认 deny）。
    """
    return _PERMISSIONS.get(role, frozenset())


class Principal(BaseModel):
    """鉴权产物（架构 §5：M02 输出 Principal）。

    由 ``AuthService.authenticate`` 产出，经 gateway 鉴权依赖注入下游 service。
    字段与 JWT claims 一一对应（TASK_BACKLOG APC-T007：user_id/family_id/role/device_id）。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: str = Field(description="成员 ULID（user.id）")
    family_id: str = Field(description="家庭 ULID（family.id）")
    role: Role = Field(description="角色（架构 §19）")
    device_id: str | None = Field(
        default=None, description="设备 ULID（device.id），System/未绑定设备时为 None"
    )


class TokenClaims(BaseModel):
    """JWT claims（TASK_BACKLOG APC-T007：user_id/family_id/role/device_id）。

    标准 claims（RFC 7519）：``iat``（签发时间）、``exp``（过期时间）、``jti``（唯一 ID）。
    业务 claims：``user_id`` / ``family_id`` / ``role`` / ``device_id``（与 ``Principal`` 对齐）。
    """

    model_config = ConfigDict(extra="forbid")

    user_id: str
    family_id: str
    role: Role
    device_id: str | None = None
    iat: datetime = Field(description="签发时间（UTC，epoch 秒）")
    exp: datetime = Field(description="过期时间（UTC，epoch 秒）")
    jti: str = Field(description="令牌唯一 ID（ULID，用于吊销/追踪）")


@runtime_checkable
class PasswordHasher(Protocol):
    """密码/PIN 哈希协议（§20 安全：不得明文存储）。

    实现负责生成 salt 与哈希校验；存储格式（算法/salt/digest）由实现自洽封装，
    调用方只感知 ``hash(plain) -> stored`` 与 ``verify(plain, stored) -> bool``。
    """

    def hash(self, plain: str) -> str:
        """对明文密码/PIN 生成可存储的哈希串（含 salt 与算法标识）。"""
        ...

    def verify(self, plain: str, stored: str) -> bool:
        """校验明文与存储哈希是否匹配（常量时间比较，防时序侧信道）。"""
        ...


@runtime_checkable
class JwtService(Protocol):
    """JWT 签发/解析协议（TASK_BACKLOG APC-T007）。

    claims SSOT：``user_id`` / ``family_id`` / ``role`` / ``device_id`` + 标准 ``iat/exp/jti``。
    实现负责签名与过期校验；解析失败（签名错误/过期/格式错）抛 ``AuthError``。
    """

    def issue(self, claims: TokenClaims) -> str:
        """签发 JWT 字符串（含签名）。"""
        ...

    def parse(self, token: str) -> TokenClaims:
        """解析并校验 JWT；失败抛 ``AuthError``（401）。"""
        ...


class UserRecord(Protocol):
    """用户记录结构协议（结构化，ORM ``User`` 与测试替身天然满足）。

    解耦领域与 ORM（架构 §5：Protocol 不绑实现），同时让 ``AuthService`` 的属性访问
    可被 mypy 检查。``role`` 为 ``str``（与 ORM ``user.role: String(32)`` 对齐）。
    """

    id: str
    family_id: str
    role: str
    display_name: str
    auth_hash: str
    is_deleted: bool


class FamilyRecord(Protocol):
    """家庭记录结构协议（结构化，ORM ``Family`` 与测试替身天然满足）。"""

    id: str
    name: str
    timezone: str
    is_deleted: bool


@runtime_checkable
class UserRepository(Protocol):
    """用户/家庭仓储协议（架构 §5.2 Repository）。

    生命周期：请求作用域（FastAPI ``Depends`` 注入 ``AsyncSession``）；
    事务边界在 service 层。本协议只定义 auth 模块所需的最小方法集。

    返回 ``UserRecord`` / ``FamilyRecord``（结构化 Protocol）而非具体 ORM 类，
    解耦领域与 ORM，同时保留 mypy 属性检查（架构 §5：Protocol 不绑实现）。
    """

    async def get_user(self, user_id: str) -> UserRecord | None:
        """按 id 取用户记录（含 family_id/role/auth_hash）；不存在返回 None。"""
        ...

    async def get_user_by_family(self, family_id: str, display_name: str) -> UserRecord | None:
        """按家庭 + 显示名取用户（登录场景：家庭内按名定位成员）。"""
        ...

    async def get_family(self, family_id: str) -> FamilyRecord | None:
        """按 id 取家庭记录；不存在返回 None。"""
        ...

    async def create_family(self, name: str, timezone: str) -> FamilyRecord:
        """创建家庭；返回记录。"""
        ...

    async def create_user(
        self, family_id: str, role: Role, display_name: str, auth_hash: str
    ) -> UserRecord:
        """创建家庭成员（auth_hash 已哈希）；返回记录。"""
        ...


class DeviceKind(StrEnum):
    """设备类型（架构 §6.1：phone/camera/mmwave/mac）。"""

    PHONE = "phone"
    CAMERA = "camera"
    MMWAVE = "mmwave"
    MAC = "mac"


class DeviceRecord(Protocol):
    """设备记录结构协议（ORM ``Device`` 与测试替身天然满足）。"""

    id: str
    family_id: str
    kind: str
    fcm_token: str | None
    meta: dict[str, Any] | None
    is_deleted: bool


@runtime_checkable
class DeviceRepository(Protocol):
    """设备仓储协议（架构 §2 M02：设备注册；§5.2 Repository 请求作用域）。

    生命周期：请求作用域（FastAPI ``Depends`` 注入 ``AsyncSession``）；事务边界在 service 层。
    """

    async def create_device(
        self,
        family_id: str,
        kind: DeviceKind,
        fcm_token: str | None,
        meta: dict[str, Any] | None,
    ) -> DeviceRecord:
        """注册设备；返回记录。``fcm_token`` 存独立字段，其余扩展信息存 ``meta`` jsonb。"""
        ...

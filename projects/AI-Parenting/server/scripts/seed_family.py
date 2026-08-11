# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# scripts/seed_family.py —— 本地种子脚本：创建默认 family、父母 Admin、baby 档案。
# 依据：ENGINEERING_DESIGN §14（Bootstrap 顺序：alembic upgrade → seed_family → 启动 FastAPI）；
#       ARCHITECTURE_FINAL §25.3（生产前清单：创建家庭账号、配置双端、录入宝宝档案）；
#       TASK_BACKLOG APC-T008。
# 设计：独立可执行脚本，复用 AuthService + SqlAlchemyUserRepository 写入 DB。
#       默认创建 1 家庭 + 父母 2 Admin + 1 baby；密码经 PBKDF2 哈希（§20 不得明文）。
#       幂等：家庭/用户已存在则跳过（按 name/display_name 去重）。
# 边界：只用于本地/开发环境初始化；prod 走正式注册流程（§25.3）。

"""本地种子脚本：创建默认 family、父母 Admin、baby 档案。

用途（ENGINEERING_DESIGN §14 Bootstrap）：``alembic upgrade head`` 后、启动 FastAPI 前，
本地初始化一套默认数据，便于开发与端到端联调。

默认创建：
    - 1 家庭（name="默认家庭"，timezone="Asia/Shanghai"）。
    - 父亲 Admin（display_name="Dad"，password 来自环境变量或默认）。
    - 母亲 Admin（display_name="Mom"，password 来自环境变量或默认）。
    - 1 baby（birth_date 默认今天，sex 默认 "unknown"）。

幂等：家庭/用户已存在则跳过（按 name/display_name 去重），不重复创建。

用法::

    python -m server.scripts.seed_family
    # 或自定义：
    PARENTING_AUTH__JWT_SECRET=... python -m server.scripts.seed_family
"""

from __future__ import annotations

import asyncio
import os
from datetime import date
from typing import Any

from sqlalchemy import select

from server.app.auth.domain import Role
from server.app.auth.infra.repository import SqlAlchemyUserRepository
from server.app.auth.service.auth_service import AuthService
from server.app.auth.service.jwt import Hs256JwtService
from server.app.auth.service.password import Pbkdf2PasswordHasher
from server.app.common.clock import SystemClock
from server.app.db import get_session_factory
from server.app.models.core import Baby, Family, User
from server.app.settings import get_settings

DEFAULT_FAMILY_NAME = os.environ.get("SEED_FAMILY_NAME", "默认家庭")
DEFAULT_TIMEZONE = os.environ.get("SEED_TIMEZONE", "Asia/Shanghai")
DEFAULT_DAD_PASSWORD = os.environ.get("SEED_DAD_PASSWORD", "admin-dad-change-me")
DEFAULT_MOM_PASSWORD = os.environ.get("SEED_MOM_PASSWORD", "admin-mom-change-me")
DEFAULT_BABY_BIRTH_DATE = os.environ.get("SEED_BABY_BIRTH_DATE", date.today().isoformat())
# sex 受 CHECK 约束 IN ('male','female')；默认 None（nullable），未指定时留空。
DEFAULT_BABY_SEX = os.environ.get("SEED_BABY_SEX") or None


async def seed() -> dict[str, str]:
    """创建默认家庭、父母 Admin、baby，返回各实体 id。

    幂等：已存在则跳过对应实体。
    """
    settings = get_settings()
    factory = get_session_factory(settings)
    async with factory() as session:
        repo = SqlAlchemyUserRepository(session)
        svc = AuthService(
            repository=repo,
            password_hasher=Pbkdf2PasswordHasher(iterations=settings.auth.password_iterations),
            jwt_service=Hs256JwtService(
                secret=settings.auth.jwt_secret, access_ttl_seconds=settings.auth.access_ttl_seconds
            ),
            clock=SystemClock(),
            access_ttl_seconds=settings.auth.access_ttl_seconds,
            session=session,
        )

        # 家庭（幂等：按 name 查未删除家庭）。
        existing_family = (
            await session.execute(
                select(Family).where(
                    Family.name == DEFAULT_FAMILY_NAME, Family.is_deleted.is_(False)
                )
            )
        ).scalar_one_or_none()
        if existing_family is None:
            family_id = await svc.create_family(name=DEFAULT_FAMILY_NAME, timezone=DEFAULT_TIMEZONE)
        else:
            family_id = existing_family.id

        # 父母 Admin（幂等：按 family_id + display_name 查）。
        dad_id = await _seed_user(svc, session, family_id, "Dad", DEFAULT_DAD_PASSWORD)
        mom_id = await _seed_user(svc, session, family_id, "Mom", DEFAULT_MOM_PASSWORD)

        # Baby（幂等：按 family_id 查未删除 baby）。
        existing_baby = (
            await session.execute(
                select(Baby).where(Baby.family_id == family_id, Baby.is_deleted.is_(False))
            )
        ).scalar_one_or_none()
        if existing_baby is None:
            baby = Baby(
                id=await _new_id(),
                family_id=family_id,
                birth_date=date.fromisoformat(DEFAULT_BABY_BIRTH_DATE),
                sex=DEFAULT_BABY_SEX,
            )
            session.add(baby)
            await session.commit()
            baby_id = baby.id
        else:
            baby_id = existing_baby.id

    return {"family_id": family_id, "dad_id": dad_id, "mom_id": mom_id, "baby_id": baby_id}


async def _seed_user(
    svc: AuthService, session: Any, family_id: str, display_name: str, password: str
) -> str:
    """幂等创建用户：已存在则返回 id，否则创建。"""
    existing = (
        await session.execute(
            select(User).where(
                User.family_id == family_id,
                User.display_name == display_name,
                User.is_deleted.is_(False),
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing.id
    return await svc.create_user(
        family_id=family_id,
        role=Role.ADMIN,
        display_name=display_name,
        plain_password=password,
    )


async def _new_id() -> str:
    from server.app.common.ids import new_id

    return new_id()


def main() -> None:
    """脚本入口：执行 seed 并打印结果。"""
    result = asyncio.run(seed())
    print("seed_family 完成：")
    print(f"  family_id: {result['family_id']}")
    print(f"  dad_id:    {result['dad_id']}  (Admin, password={DEFAULT_DAD_PASSWORD})")
    print(f"  mom_id:    {result['mom_id']}  (Admin, password={DEFAULT_MOM_PASSWORD})")
    print(f"  baby_id:   {result['baby_id']}")
    print("提示：prod 请走正式注册流程，勿用默认密码（§25.3）。")


if __name__ == "__main__":
    main()

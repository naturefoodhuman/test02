# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 19:12:00

"""Seed a local family/admin/baby for dev or PostgreSQL-backed runs.

Without a database URL the script keeps the original in-memory behavior, which is
useful for quick smoke output. When `--database-url` or `PARENTING_DATABASE__URL`
is present it writes family/user/baby rows through the SQLAlchemy Auth adapter so
Android and API DB smoke tests can reuse the generated IDs.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.app.auth.infra.repository import InMemoryAuthRepository  # noqa: E402
from server.app.auth.infra.sqlalchemy_repository import SQLAlchemyAuthRepository  # noqa: E402
from server.app.auth.service.auth_service import AuthService  # noqa: E402
from server.app.auth.service.jwt_service import JWTService  # noqa: E402
from server.app.auth.service.passwords import PasswordHasher  # noqa: E402
from server.app.common.ids import new_ulid  # noqa: E402
from server.app.db import create_engine, create_session_factory  # noqa: E402
from server.app.settings import Settings  # noqa: E402


def _service(
    repository: InMemoryAuthRepository | SQLAlchemyAuthRepository,
    jwt_secret: str,
) -> AuthService:
    return AuthService(
        repository,
        JWTService(jwt_secret),
        PasswordHasher(iterations=10_000),
    )


async def _seed_with_repository(
    repository: InMemoryAuthRepository | SQLAlchemyAuthRepository,
    args: argparse.Namespace,
    jwt_secret: str,
    *,
    mode: str,
) -> dict[str, Any]:
    service = _service(repository, jwt_secret)
    family, admin = await service.create_family_with_admin(
        family_name=args.family_name,
        admin_display_name=args.admin_display_name,
        admin_secret=args.admin_secret,
        timezone=args.timezone,
    )
    baby_id: str | None = None
    if not args.no_baby:
        baby_id = new_ulid()
        if isinstance(repository, SQLAlchemyAuthRepository):
            await repository.add_baby(family_id=family.id, baby_id=baby_id, name=args.baby_name)
    login = await service.authenticate(
        family_id=family.id,
        display_name=admin.display_name,
        secret=args.admin_secret,
    )
    result: dict[str, Any] = {
        "mode": mode,
        "family_id": family.id,
        "admin_user_id": admin.id,
        "access_token": login.access_token,
        "token_type": "bearer",
    }
    if baby_id is not None:
        result["baby_id"] = baby_id
        result["baby_name"] = args.baby_name
    if mode == "in-memory":
        result["note"] = (
            "In-memory seed only; pass --database-url or PARENTING_DATABASE__URL to persist."
        )
    return result


async def seed(args: argparse.Namespace) -> dict[str, Any]:
    settings = Settings()
    if args.database_url:
        settings.database.url = args.database_url
    jwt_secret = args.jwt_secret or settings.auth.jwt_secret

    if settings.database.url:
        engine = create_engine(settings.database)
        session_factory = create_session_factory(engine)
        try:
            async with session_factory() as session:
                async with session.begin():
                    return await _seed_with_repository(
                        SQLAlchemyAuthRepository(session),
                        args,
                        jwt_secret,
                        mode="database",
                    )
        finally:
            await engine.dispose()

    return await _seed_with_repository(
        InMemoryAuthRepository(),
        args,
        jwt_secret,
        mode="in-memory",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family-name", default="Demo Family")
    parser.add_argument("--admin-display-name", default="Admin")
    parser.add_argument("--admin-secret", default="change-me-local")
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument("--baby-name", default="Baby")
    parser.add_argument("--no-baby", action="store_true")
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--jwt-secret", default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(json.dumps(asyncio.run(seed(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

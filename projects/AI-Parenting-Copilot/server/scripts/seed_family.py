# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 01:15:00


"""Seed a dev family using the in-memory AuthService.

APC-T008 real database seeding remains blocked until PostgreSQL validation lands.
This script is still useful for generating deterministic sample payloads and
validating the Auth service without real DB state.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.app.auth.infra.repository import InMemoryAuthRepository  # noqa: E402
from server.app.auth.service.auth_service import AuthService  # noqa: E402
from server.app.auth.service.jwt_service import JWTService  # noqa: E402
from server.app.auth.service.passwords import PasswordHasher  # noqa: E402


async def seed(args: argparse.Namespace) -> dict[str, str]:
    service = AuthService(
        InMemoryAuthRepository(),
        JWTService(args.jwt_secret),
        PasswordHasher(iterations=10_000),
    )
    family, admin = await service.create_family_with_admin(
        family_name=args.family_name,
        admin_display_name=args.admin_display_name,
        admin_secret=args.admin_secret,
    )
    login = await service.authenticate(
        family_id=family.id,
        display_name=admin.display_name,
        secret=args.admin_secret,
    )
    return {
        "family_id": family.id,
        "admin_user_id": admin.id,
        "access_token": login.access_token,
        "note": "In-memory seed only; DB persistence waits for APC-T003/T004 validation.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family-name", default="Demo Family")
    parser.add_argument("--admin-display-name", default="Admin")
    parser.add_argument("--admin-secret", default="change-me-local")
    parser.add_argument("--jwt-secret", default="dev-secret-change-me-at-least-16")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(seed(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

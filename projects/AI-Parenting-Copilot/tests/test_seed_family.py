# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 19:13:00

"""APC-T008 seed_family script smoke tests."""

from __future__ import annotations

import asyncio

from server.scripts.seed_family import build_parser, seed


def test_seed_family_defaults_to_in_memory_with_baby() -> None:
    args = build_parser().parse_args(
        [
            "--family-name",
            "Seed Test Family",
            "--admin-display-name",
            "Seed Admin",
            "--admin-secret",
            "secret123",
        ]
    )

    result = asyncio.run(seed(args))

    assert result["mode"] == "in-memory"
    assert result["family_id"]
    assert result["admin_user_id"]
    assert result["baby_id"]
    assert result["baby_name"] == "Baby"
    assert result["access_token"]


def test_seed_family_can_skip_baby() -> None:
    args = build_parser().parse_args(
        [
            "--admin-secret",
            "secret123",
            "--no-baby",
        ]
    )

    result = asyncio.run(seed(args))

    assert result["mode"] == "in-memory"
    assert "baby_id" not in result

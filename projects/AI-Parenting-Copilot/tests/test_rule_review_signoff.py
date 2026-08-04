# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 22:58:00

"""Rule review sign-off artifact tests."""

from __future__ import annotations

from server.app.rule_engine.review_signoff import (
    build_signoff_template,
    validate_rule_signoff,
)


def test_rule_signoff_template_contains_current_hash_and_checklist() -> None:
    template = build_signoff_template("vaccine")

    assert template.domain == "vaccine"
    assert len(template.pack_hash) == 64
    assert "official_source_verified" in template.checklist
    assert template.status == "pending"


def test_dev_shadow_signoff_can_validate_current_fixture_with_warning() -> None:
    signoff = build_signoff_template("vaccine")
    approved = signoff.__class__(
        **{
            **signoff.to_dict(),
            "status": "approved",
            "reviewer": "reviewer-1",
            "reviewed_at": "2026-08-04T00:00:00+08:00",
            "checklist": {key: True for key in signoff.checklist},
        }
    )

    result = validate_rule_signoff(approved)

    assert result.ok is True
    assert "not production approval" in result.warnings[0]


def test_production_signoff_rejects_current_dev_fixture_pack() -> None:
    signoff = build_signoff_template("growth", scope="production")
    approved = signoff.__class__(
        **{
            **signoff.to_dict(),
            "status": "approved",
            "reviewer": "reviewer-1",
            "reviewed_at": "2026-08-04T00:00:00+08:00",
            "checklist": {key: True for key in signoff.checklist},
        }
    )

    result = validate_rule_signoff(approved)

    assert result.ok is False
    assert "production signoff cannot approve dev fixture rule pack" in result.errors


def test_signoff_rejects_hash_mismatch() -> None:
    signoff = build_signoff_template("vaccine")
    bad = signoff.__class__(
        **{
            **signoff.to_dict(),
            "status": "approved",
            "reviewer": "reviewer-1",
            "reviewed_at": "2026-08-04T00:00:00+08:00",
            "pack_hash": "0" * 64,
            "checklist": {key: True for key in signoff.checklist},
        }
    )

    result = validate_rule_signoff(bad)

    assert result.ok is False
    assert "pack_hash mismatch" in result.errors

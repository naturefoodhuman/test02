# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 22:10:00

"""External validation plan tests for remaining local-only blockers."""

from __future__ import annotations

from server.app.ops.external_validation import build_external_validation_plan


def test_external_validation_plan_covers_remaining_hardware_and_review_blockers() -> None:
    plan = build_external_validation_plan()
    task_ids = {item.task_id for item in plan.items}

    assert plan.status == "waiting_for_external_validation"
    assert {
        "APC-T022",
        "APC-T023",
        "APC-T038",
        "APC-T039",
        "APC-T040",
        "APC-T041",
        "APC-T044",
        "APC-T059",
    }.issubset(task_ids)
    assert plan.summary["human_medical_review"] == 2
    assert plan.summary["camera_device"] == 1
    assert all(item.commands for item in plan.items)
    assert all(item.evidence_required for item in plan.items)
    assert all(item.success_criteria for item in plan.items)


def test_external_validation_plan_markdown_mentions_not_substitute() -> None:
    markdown = build_external_validation_plan().to_markdown()

    assert "not be treated as substitutes" in markdown
    assert "APC-T044" in markdown
    assert "pg_restore --list" in markdown

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 15:20:00

"""Static tests for SQLAlchemy DB repository adapters."""
from __future__ import annotations

from pathlib import Path


def test_sqlalchemy_repository_adapters_exist_for_core_blocked_tasks() -> None:
    files = [
        Path("server/app/auth/infra/sqlalchemy_repository.py"),
        Path("server/app/events/infra/sqlalchemy_repository.py"),
        Path("server/app/notification/sqlalchemy_alert_repo.py"),
    ]

    for path in files:
        assert path.exists(), path
        text = path.read_text()
        assert "AsyncSession" in text
        assert "select(" in text


def test_event_repository_adapter_preserves_idempotency_and_soft_delete_hooks() -> None:
    text = Path("server/app/events/infra/sqlalchemy_repository.py").read_text()

    assert "ensure_idempotent" in text
    assert "is_deleted = True" in text
    assert "correction_of=original.event_id" in text


def test_alert_repository_adapter_has_ack_and_feedback_paths() -> None:
    text = Path("server/app/notification/sqlalchemy_alert_repo.py").read_text()

    assert "AlertStatus.ACKNOWLEDGED" in text
    assert "request.feedback.value" in text

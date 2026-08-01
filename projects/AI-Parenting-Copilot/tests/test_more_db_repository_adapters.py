# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 16:05:00

"""Static tests for additional SQLAlchemy repository adapters."""

from __future__ import annotations

from pathlib import Path


def test_additional_sqlalchemy_adapters_exist() -> None:
    files = [
        Path("server/app/state_engine/sqlalchemy_snapshot_repo.py"),
        Path("server/app/rule_engine/sqlalchemy_evidence_repo.py"),
        Path("server/app/media/sqlalchemy_media_repo.py"),
        Path("server/app/notification/sqlalchemy_delivery_repo.py"),
        Path("server/app/camera/sqlalchemy_sleep_session_repo.py"),
        Path("server/app/mmwave/sqlalchemy_sensor_event_repo.py"),
        Path("server/app/camera/sqlalchemy_camera_event_repo.py"),
    ]

    for path in files:
        text = path.read_text()
        assert "AsyncSession" in text
        assert "select(" in text or "session.add" in text


def test_state_and_evidence_adapters_preserve_upsert_and_activate_paths() -> None:
    state = Path("server/app/state_engine/sqlalchemy_snapshot_repo.py").read_text()
    evidence = Path("server/app/rule_engine/sqlalchemy_evidence_repo.py").read_text()

    assert "upsert" in state
    assert "ORMDerivedBabyState" in state
    assert "effective_to" in evidence
    assert "pack.compute_hash()" in evidence


def test_media_delivery_sleep_adapters_preserve_metadata_paths() -> None:
    media = Path("server/app/media/sqlalchemy_media_repo.py").read_text()
    delivery = Path("server/app/notification/sqlalchemy_delivery_repo.py").read_text()
    sleep = Path("server/app/camera/sqlalchemy_sleep_session_repo.py").read_text()

    sensor = Path("server/app/mmwave/sqlalchemy_sensor_event_repo.py").read_text()
    camera = Path("server/app/camera/sqlalchemy_camera_event_repo.py").read_text()

    assert "content_type" in media
    assert "thumbnail_path" in media
    assert "DeliveryReceipt" in delivery
    assert "roi_config" in sleep
    assert "SensorEventCandidate" in sensor
    assert "CameraEventRecord" in camera

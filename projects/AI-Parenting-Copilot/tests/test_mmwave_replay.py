# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 04:45:00

"""mmWave fixture replay report tests."""

from __future__ import annotations

from pathlib import Path

from server.app.mmwave.replay import replay_mmwave_fixture


def test_mmwave_replay_report_counts_fixture_signals() -> None:
    report = replay_mmwave_fixture(Path("tests/fixtures/radar_frames.jsonl"))

    assert report.total_frames == 2
    assert report.presence_count == 2
    assert report.abnormal_count == 1
    assert report.observation_count == 2
    assert report.signal_type_counts["moving"] == 1
    assert report.signal_type_counts["apnea_candidate"] == 1
    assert all(frame.observation_event_type == "mmwave_telemetry" for frame in report.frames)


def test_mmwave_replay_report_can_disable_observation_mapping() -> None:
    report = replay_mmwave_fixture(
        Path("tests/fixtures/radar_frames.jsonl"),
        baby_id=None,
        family_id=None,
    )

    assert report.total_frames == 2
    assert report.observation_count == 0

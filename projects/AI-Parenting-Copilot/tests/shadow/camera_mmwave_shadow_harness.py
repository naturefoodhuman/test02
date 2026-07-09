# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 14:30:00

"""7-night camera/mmWave shadow-mode harness.

The harness is deterministic and uses fixture data by default. It never creates strong
alerts; it only reports shadow candidates and feedback statistics.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from server.app.camera.fusion import FusionInput, FusionStateMachine
from server.app.mmwave.frame_parser import parse_jsonl


@dataclass(slots=True)
class ShadowCandidate:
    frame_index: int
    reason_code: str
    evidence: dict[str, object]
    feedback: str | None = None
    alert_level: str | None = None


@dataclass(slots=True)
class ShadowReport:
    fixture: str
    total_frames: int
    candidates: list[ShadowCandidate] = field(default_factory=list)

    @property
    def false_positive_count(self) -> int:
        return sum(1 for candidate in self.candidates if candidate.feedback == "false_positive")

    @property
    def false_positive_rate(self) -> float:
        if not self.candidates:
            return 0.0
        return self.false_positive_count / len(self.candidates)

    def to_dict(self) -> dict[str, object]:
        return {
            "fixture": self.fixture,
            "total_frames": self.total_frames,
            "candidate_count": len(self.candidates),
            "false_positive_count": self.false_positive_count,
            "false_positive_rate": self.false_positive_rate,
            "candidates": [asdict(candidate) for candidate in self.candidates],
        }


def run_shadow_fixture(
    fixture: Path,
    *,
    camera_kind: str | None = "face_covered",
    active_session: bool = True,
) -> ShadowReport:
    frames = parse_jsonl(fixture.read_text(encoding="utf-8"))
    fusion = FusionStateMachine()
    report = ShadowReport(fixture=str(fixture), total_frames=len(frames))
    for index, frame in enumerate(frames):
        decision = fusion.evaluate(
            FusionInput(
                sleep_session_active=active_session,
                camera_kind=camera_kind if frame.abnormal_event else None,
                camera_confidence=0.9 if frame.abnormal_event else None,
                mmwave_abnormal_event=frame.abnormal_event,
            )
        )
        if decision.shadow_event:
            report.candidates.append(
                ShadowCandidate(
                    frame_index=index,
                    reason_code=decision.reason_code,
                    evidence=decision.evidence,
                    alert_level=decision.alert_level,
                )
            )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="tests/fixtures/radar_frames.jsonl")
    parser.add_argument("--output", default="runtime/shadow_report.json")
    args = parser.parse_args()
    report = run_shadow_fixture(Path(args.fixture))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report.to_dict(), ensure_ascii=False))


if __name__ == "__main__":
    main()

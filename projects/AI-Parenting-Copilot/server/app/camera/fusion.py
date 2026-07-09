# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 07:55:00


"""Camera/mmWave fusion state machine for shadow-mode safety signals."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class FusionInput:
    sleep_session_active: bool
    camera_kind: str | None = None
    camera_confidence: float | None = None
    mmwave_abnormal_event: str | None = None
    parent_present: bool = False


@dataclass(frozen=True, slots=True)
class FusionDecision:
    shadow_event: bool
    reason_code: str
    evidence: dict[str, object] = field(default_factory=dict)
    alert_level: str | None = None


class FusionStateMachine:
    """P0 shadow-mode fusion; never emits red alerts."""

    def evaluate(self, fusion_input: FusionInput) -> FusionDecision:
        if not fusion_input.sleep_session_active:
            return FusionDecision(False, "sleep_session_not_active")
        if fusion_input.mmwave_abnormal_event and not fusion_input.camera_kind:
            return FusionDecision(
                True,
                "mmwave_shadow_only_requires_visual_confirmation",
                {"mmwave_abnormal_event": fusion_input.mmwave_abnormal_event},
                alert_level=None,
            )
        if (
            fusion_input.camera_kind in {"face_covered", "prone"}
            and fusion_input.mmwave_abnormal_event
        ):
            return FusionDecision(
                True,
                "multi_signal_shadow_candidate",
                {
                    "camera_kind": fusion_input.camera_kind,
                    "camera_confidence": fusion_input.camera_confidence,
                    "mmwave_abnormal_event": fusion_input.mmwave_abnormal_event,
                },
                alert_level="shadow",
            )
        return FusionDecision(False, "no_shadow_signal")

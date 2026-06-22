# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 21:15:00

"""
PrivacyGateway orchestration pipeline (E5-C9-S1-T1).

Per NETWORK_ARCHITECTURE_FINAL.md §10.2 and NETWORK_ENGINEERING_DESIGN.md §7.4.

Pipeline:
1. Unicode normalize
2. Presidio / deterministic regex detectors
3. spaCy NER
4. Qwen3 auxiliary classifier
5. Placeholder replacement
6. JSON Schema validation
7. Canary token detection

This module composes already-implemented E5-C1~E5-C8 components without
changing their responsibilities. It intentionally does not expose the factory
function requested by E5-C9-S1-T2; that remains the next task.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Literal, Mapping, Optional

from _infra.network.utils.unicode_norm import normalize_for_pii_detection

from .canary import CanaryTokenMonitor
from .detectors.base import PIIDetector
from .detectors.ner_detector import SpaCyNERDetector
from .detectors.qwen_classifier import QwenPIIClassifier, QwenPIIResult
from .models import PIIEntity
from .recognizers.secret_recognizers import detect_secrets
from .replacer import PIIReplacer
from .validator import PrivacyOutputValidator, build_privacy_output


@dataclass(frozen=True)
class PrivacyContext:
    """Privacy Gateway processing context."""

    mode: Literal["light", "full"] = "light"
    source_url: str = "unknown"
    require_schema_validation: bool = True


@dataclass(frozen=True)
class RedactedContent:
    """Schema-safe Privacy Gateway output plus local execution metadata."""

    text: str
    pii_map_id: str
    detections: list[dict[str, Any]]
    schema_valid: bool
    canary_clean: bool
    mode: str
    source_url: str
    warnings: list[str] = field(default_factory=list)
    qwen_result: QwenPIIResult | None = None

    def to_output_dict(self) -> dict[str, Any]:
        """Return only schema-controlled fields intended for downstream output."""
        return {
            "text": self.text,
            "mapping_id": self.pii_map_id,
            "entities": self.detections,
            "schema_valid": self.schema_valid,
            "canary_clean": self.canary_clean,
        }


class PrivacyGateway:
    """Orchestrates E5 Privacy Gateway layers L1-L7."""

    def __init__(
        self,
        detectors: Iterable[PIIDetector] | None = None,
        ner_detector: PIIDetector | None = None,
        qwen_classifier: QwenPIIClassifier | None = None,
        replacer: PIIReplacer | None = None,
        output_validator: PrivacyOutputValidator | None = None,
        canary_monitor: CanaryTokenMonitor | None = None,
        enable_presidio_default: bool = True,
        enable_ner_default: bool = True,
        enable_qwen_default: bool = False,
    ):
        self.detectors: list[PIIDetector] = list(detectors or [])
        self.warnings: list[str] = []

        if detectors is None and enable_presidio_default:
            presidio = self._try_build_presidio_detector()
            if presidio is not None:
                self.detectors.append(presidio)

        if ner_detector is not None:
            self.ner_detector = ner_detector
        elif enable_ner_default:
            self.ner_detector = SpaCyNERDetector()
        else:
            self.ner_detector = None

        if qwen_classifier is not None:
            self.qwen_classifier = qwen_classifier
        elif enable_qwen_default:
            self.qwen_classifier = QwenPIIClassifier()
        else:
            self.qwen_classifier = None

        self.replacer = replacer or PIIReplacer()
        self.output_validator = output_validator or PrivacyOutputValidator()
        self.canary_monitor = canary_monitor or CanaryTokenMonitor.from_config()

    @staticmethod
    def _try_build_presidio_detector() -> PIIDetector | None:
        try:
            from .detectors.presidio_detector import PresidioDetector

            return PresidioDetector(language="en")
        except Exception:
            return None

    @staticmethod
    def _extract_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        text = getattr(content, "text", None)
        if isinstance(text, str):
            return text
        return str(content or "")

    async def _run_detector(self, detector: PIIDetector, text: str, warnings: list[str]) -> list[PIIEntity]:
        try:
            return await detector.detect(text)
        except Exception as exc:
            warnings.append(f"detector_failed:{detector.get_name()}:{type(exc).__name__}")
            return []

    async def process(self, content: Any, ctx: PrivacyContext) -> RedactedContent:
        """Run Privacy Gateway L1-L7 and return schema-safe redacted content."""
        warnings: list[str] = []

        raw_text = self._extract_text(content)

        # L1: Unicode normalize
        normalized_text = normalize_for_pii_detection(raw_text)

        # L2: Presidio / custom recognizers / deterministic secret regex
        entities: list[PIIEntity] = []
        for detector in self.detectors:
            entities.extend(await self._run_detector(detector, normalized_text, warnings))
        entities.extend(detect_secrets(normalized_text))

        # L3: spaCy NER
        if self.ner_detector is not None:
            entities.extend(await self._run_detector(self.ner_detector, normalized_text, warnings))

        # L4: Qwen3 auxiliary review (never sole security boundary)
        qwen_result: QwenPIIResult | None = None
        if self.qwen_classifier is not None:
            qwen_result = await self.qwen_classifier.classify(normalized_text)
            if qwen_result.degraded:
                warnings.append("qwen_classifier_degraded")
            elif qwen_result.contains_pii and not entities:
                warnings.append(f"qwen_classifier_flagged:{qwen_result.classification.value}:no_spans")

        # L5: Placeholder replacement + local mapping store
        replacement = self.replacer.replace(normalized_text, entities)

        # L6: JSON Schema output validation
        output = build_privacy_output(
            replacement.text,
            replacement.mapping_id,
            replacement.mapping,
            schema_valid=ctx.require_schema_validation,
            canary_clean=True,
        )
        if ctx.require_schema_validation:
            self.output_validator.validate(output)

        # L7: Canary token detection on final redacted output
        self.canary_monitor.assert_clean(output["text"], location=f"privacy_gateway:{ctx.source_url}")

        return RedactedContent(
            text=output["text"],
            pii_map_id=output["mapping_id"],
            detections=output["entities"],
            schema_valid=bool(ctx.require_schema_validation),
            canary_clean=True,
            mode=ctx.mode,
            source_url=ctx.source_url,
            warnings=warnings,
            qwen_result=qwen_result,
        )

    async def process_text(
        self,
        text: str,
        mode: Literal["light", "full"] = "light",
        source_url: str = "unknown",
    ) -> RedactedContent:
        """Convenience method for direct text processing."""
        return await self.process(text, PrivacyContext(mode=mode, source_url=source_url))


__all__ = ["PrivacyContext", "PrivacyGateway", "RedactedContent"]

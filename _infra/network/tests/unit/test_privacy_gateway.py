# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 21:30:00

"""Unit/integration-style tests for PrivacyGateway orchestration (E5-C9-S1-T1)."""

import asyncio

import pytest

from _infra.network.exceptions import CanaryTokenDetectedError, SchemaValidationFailedError
from _infra.network.input_sanitizer.sanitizer import SanitizedContent
from _infra.network.privacy_gateway.canary import CanaryTokenMonitor
from _infra.network.privacy_gateway.detectors.base import PIIDetector
from _infra.network.privacy_gateway.detectors.qwen_classifier import QwenPIIClassification, QwenPIIResult
from _infra.network.privacy_gateway.gateway import PrivacyContext, PrivacyGateway
from _infra.network.privacy_gateway.models import PIIEntity, PIIType
from _infra.network.privacy_gateway.replacer import InMemoryPIIMapStore, PIIReplacer
from _infra.network.privacy_gateway.validator import PrivacyOutputValidator


class StaticDetector(PIIDetector):
    def __init__(self, entity_specs):
        self.entity_specs = entity_specs

    async def detect(self, text: str):
        entities = []
        for entity_type, value, recognizer in self.entity_specs:
            start = text.find(value)
            if start >= 0:
                entities.append(
                    PIIEntity(
                        type=entity_type,
                        value=value,
                        start=start,
                        end=start + len(value),
                        recognizer=recognizer,
                        score=0.95,
                    )
                )
        return entities


class FailingDetector(PIIDetector):
    async def detect(self, text: str):
        raise RuntimeError("detector boom")

    def get_name(self) -> str:
        return "failing"


class FakeQwenClassifier:
    def __init__(self, result: QwenPIIResult):
        self.result = result
        self.calls = []

    async def classify(self, text: str):
        self.calls.append(text)
        return self.result


def run(coro):
    return asyncio.run(coro)


def test_privacy_gateway_full_pipeline_redacts_and_validates():
    store = InMemoryPIIMapStore()
    gateway = PrivacyGateway(
        detectors=[StaticDetector([(PIIType.PERSON, "Alice", "test:person")])],
        ner_detector=StaticDetector([(PIIType.ORGANIZATION, "OpenAI", "test:org")]),
        qwen_classifier=FakeQwenClassifier(QwenPIIResult(QwenPIIClassification.NO, raw_response="否")),
        replacer=PIIReplacer(store=store),
        canary_monitor=CanaryTokenMonitor(tokens=["CANARY_TEST"]),
        enable_presidio_default=False,
        enable_ner_default=False,
    )

    result = run(gateway.process_text("Alice works at OpenAI.", source_url="unit://source"))

    assert result.text == "PII_PERSON_001 works at PII_ORGANIZATION_002."
    assert "Alice" not in result.text
    assert "OpenAI" not in result.text
    assert result.schema_valid is True
    assert result.canary_clean is True
    assert result.source_url == "unit://source"
    assert [entity["placeholder"] for entity in result.detections] == [
        "PII_PERSON_001",
        "PII_ORGANIZATION_002",
    ]
    assert store.has(result.pii_map_id) is True


def test_privacy_gateway_l1_unicode_normalization_before_detection():
    gateway = PrivacyGateway(
        detectors=[StaticDetector([(PIIType.CN_PHONE, "13812345678", "test:phone")])],
        ner_detector=None,
        canary_monitor=CanaryTokenMonitor(tokens=["CANARY_TEST"]),
        enable_presidio_default=False,
        enable_ner_default=False,
    )

    # Full-width digits should normalize before detector offsets are evaluated.
    result = run(gateway.process_text("电话：１３８１２３４５６７８"))

    assert result.text == "电话:PII_CN_PHONE_001"
    assert result.detections[0]["type"] == "CN_PHONE"


def test_privacy_gateway_l2_secret_regex_detects_without_external_dependencies():
    gateway = PrivacyGateway(
        detectors=[],
        ner_detector=None,
        canary_monitor=CanaryTokenMonitor(tokens=["CANARY_TEST"]),
        enable_presidio_default=False,
        enable_ner_default=False,
    )

    result = run(gateway.process_text("key sk-proj-abcdefghijklmnopqrstuvwxyz123456 leaked"))

    assert "sk-proj" not in result.text
    assert result.detections[0]["type"] == "API_KEY"


def test_privacy_gateway_canary_blocks_final_output():
    gateway = PrivacyGateway(
        detectors=[],
        ner_detector=None,
        canary_monitor=CanaryTokenMonitor(tokens=["AI_CANARY_DO_NOT_LEAK_2026"]),
        enable_presidio_default=False,
        enable_ner_default=False,
    )

    with pytest.raises(CanaryTokenDetectedError):
        run(gateway.process_text("AI_CANARY_DO_NOT_LEAK_2026_secret"))


def test_privacy_gateway_detector_failure_degrades_with_warning():
    gateway = PrivacyGateway(
        detectors=[FailingDetector()],
        ner_detector=None,
        canary_monitor=CanaryTokenMonitor(tokens=["CANARY_TEST"]),
        enable_presidio_default=False,
        enable_ner_default=False,
    )

    result = run(gateway.process_text("safe text"))

    assert result.text == "safe text"
    assert any(warning.startswith("detector_failed:failing") for warning in result.warnings)


def test_privacy_gateway_qwen_uncertain_no_spans_warns_but_does_not_block():
    gateway = PrivacyGateway(
        detectors=[],
        ner_detector=None,
        qwen_classifier=FakeQwenClassifier(QwenPIIResult(QwenPIIClassification.UNCERTAIN, raw_response="不确定")),
        canary_monitor=CanaryTokenMonitor(tokens=["CANARY_TEST"]),
        enable_presidio_default=False,
        enable_ner_default=False,
    )

    result = run(gateway.process_text("ambiguous text"))

    assert result.text == "ambiguous text"
    assert "qwen_classifier_flagged:uncertain:no_spans" in result.warnings
    assert result.qwen_result is not None


def test_privacy_gateway_accepts_sanitized_content_and_full_mode():
    gateway = PrivacyGateway(
        detectors=[StaticDetector([(PIIType.PERSON, "Alice", "test:person")])],
        ner_detector=None,
        canary_monitor=CanaryTokenMonitor(tokens=["CANARY_TEST"]),
        enable_presidio_default=False,
        enable_ner_default=False,
    )
    content = SanitizedContent(text="Alice", source_url="unit://sanitized")

    result = run(gateway.process(content, PrivacyContext(mode="full", source_url=content.source_url)))

    assert result.mode == "full"
    assert result.text == "PII_PERSON_001"


def test_privacy_gateway_schema_failure_propagates():
    bad_schema = {
        "type": "object",
        "required": ["must_exist"],
        "properties": {"must_exist": {"type": "string"}},
        "additionalProperties": False,
    }
    gateway = PrivacyGateway(
        detectors=[],
        ner_detector=None,
        output_validator=PrivacyOutputValidator(schema=bad_schema),
        canary_monitor=CanaryTokenMonitor(tokens=["CANARY_TEST"]),
        enable_presidio_default=False,
        enable_ner_default=False,
    )

    with pytest.raises(SchemaValidationFailedError):
        run(gateway.process_text("safe"))


def test_build_privacy_gateway_from_mapping_config_without_secret_falls_back(monkeypatch):
    from _infra.network.config_loader.schemas import NetworkConfig
    from _infra.network.privacy_gateway.gateway import build_privacy_gateway

    monkeypatch.delenv("PII_MAP_ENCRYPTION_KEY", raising=False)
    cfg = NetworkConfig(
        privacy_gateway={
            "qwen_model": "qwen3:test",
            "qwen_base_url": "http://127.0.0.1:11434",
            "qwen_timeout_seconds": 10,
            "spacy_model": "zh_core_web_sm",
            "pii_map_db": "runtime/test_pii_map.db",
            "pii_map_encryption_key_env": "PII_MAP_ENCRYPTION_KEY",
            "canary_tokens": ["FACTORY_CANARY"],
            "output_schema_strict": True,
            "placeholder_format": "<<{entity_type}_{index}>>",
        }
    )

    gateway = build_privacy_gateway(
        cfg,
        enable_presidio=False,
        enable_ner=False,
        enable_qwen=True,
    )

    assert gateway.qwen_classifier.model == "qwen3:test"
    assert gateway.qwen_classifier.timeout == 10.0
    assert gateway.replacer.placeholder_format == "<<{entity_type}_{index}>>"
    assert gateway.canary_monitor.has_canary("FACTORY_CANARY") is True
    assert any(warning.startswith("pii_map_db_fallback:missing_secret") for warning in gateway.warnings)

    result = run(gateway.process_text("key sk-proj-abcdefghijklmnopqrstuvwxyz123456"))
    assert "sk-proj" not in result.text
    assert result.text == "key <<API_KEY_1>>"


def test_build_privacy_gateway_uses_encrypted_pii_map_db_when_key_present(tmp_path, monkeypatch):
    from _infra.network.config_loader.schemas import NetworkConfig
    from _infra.network.privacy_gateway.gateway import build_privacy_gateway
    from _infra.network.privacy_gateway.pii_map_db import PIIMapDB

    monkeypatch.setenv("TEST_PII_KEY", "factory-test-key-at-least-16")
    db_path = tmp_path / "pii_map.db"
    cfg = NetworkConfig(
        privacy_gateway={
            "pii_map_db": str(db_path),
            "pii_map_encryption_key_env": "TEST_PII_KEY",
            "canary_tokens": ["FACTORY_CANARY"],
            "placeholder_format": "PII_{entity_type}_{index:03d}",
        }
    )

    gateway = build_privacy_gateway(
        cfg,
        enable_presidio=False,
        enable_ner=False,
        enable_qwen=False,
    )

    assert isinstance(gateway.replacer.store, PIIMapDB)
    result = run(gateway.process_text("Alice", source_url="factory://unit"))
    # No detectors were enabled, so mapping is empty but DB is initialized.
    assert result.text == "Alice"
    assert db_path.exists()

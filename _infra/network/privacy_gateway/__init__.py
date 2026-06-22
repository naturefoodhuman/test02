# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 21:15:00

"""
Privacy Gateway module (FORGE Network incremental).

M-07: 7-layer PII detection pipeline.

Core exports:
- PIIType, PIIEntity (models)
- PIIDetector (ABC)
- PIIReplacer (placeholder replacement)
- PIIMapDB (encrypted mapping persistence)
- PrivacyOutputValidator (JSON Schema output validation)
- CanaryTokenMonitor (canary leak detection)
- PrivacyGateway (L1-L7 orchestration)

Concrete detectors with optional heavy dependencies (for example
PresidioDetector / presidio_analyzer, spaCy models, Ollama) are lazy-loaded from
subpackages so base models and deterministic replacement stay independently
importable and testable.
"""

from .canary import CanaryHit, CanaryTokenMonitor
from .detectors import PIIDetector
from .gateway import PrivacyContext, PrivacyGateway, RedactedContent
from .models import PIIEntity, PIIType
from .pii_map_db import PIIMapDB, PIIMapDBConfig, PIIMapDecryptionError
from .replacer import InMemoryPIIMapStore, PIIPlaceholderMapping, PIIReplacementResult, PIIReplacer
from .validator import PrivacyOutputValidator, build_privacy_output, validate_privacy_output

__all__ = [
    "CanaryHit",
    "CanaryTokenMonitor",
    "InMemoryPIIMapStore",
    "PIIEntity",
    "PIIDetector",
    "PIIMapDB",
    "PIIMapDBConfig",
    "PIIMapDecryptionError",
    "PIIPlaceholderMapping",
    "PIIReplacementResult",
    "PIIReplacer",
    "PIIType",
    "PrivacyContext",
    "PrivacyGateway",
    "PrivacyOutputValidator",
    "RedactedContent",
    "build_privacy_output",
    "validate_privacy_output",
]

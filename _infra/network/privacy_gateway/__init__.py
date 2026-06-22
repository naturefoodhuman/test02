# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 20:18:00

"""
Privacy Gateway module (FORGE Network incremental).

M-07: 7-layer PII detection pipeline.

Core exports:
- PIIType, PIIEntity (models)
- PIIDetector (ABC)
- PIIReplacer (placeholder replacement)

Concrete detectors with optional heavy dependencies (for example
PresidioDetector / presidio_analyzer, spaCy models, Ollama) are lazy-loaded from
subpackages so base models and deterministic replacement stay independently
importable and testable.
"""

from .detectors import PIIDetector
from .models import PIIEntity, PIIType
from .replacer import InMemoryPIIMapStore, PIIPlaceholderMapping, PIIReplacementResult, PIIReplacer

__all__ = [
    "InMemoryPIIMapStore",
    "PIIEntity",
    "PIIDetector",
    "PIIPlaceholderMapping",
    "PIIReplacementResult",
    "PIIReplacer",
    "PIIType",
]

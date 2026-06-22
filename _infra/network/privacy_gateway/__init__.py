# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 19:32:46

"""
Privacy Gateway module (FORGE Network incremental).

M-07: 7-layer PII detection pipeline.

Core exports:
- PIIType, PIIEntity (models)
- PIIDetector (ABC)

Concrete detectors with optional heavy dependencies (for example
PresidioDetector / presidio_analyzer) are intentionally lazy-loaded from the
``privacy_gateway.detectors`` subpackage so the base models and ABC remain
independently importable and testable.
"""

from .detectors import PIIDetector
from .models import PIIEntity, PIIType

__all__ = [
    "PIIEntity",
    "PIIDetector",
    "PIIType",
]

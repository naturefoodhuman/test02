# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 20:05:00

"""
Detectors subpackage for Privacy Gateway (E5-C3/E5-C4/E5-C5).

Exports:
- PIIDetector (ABC)
- PresidioDetector (concrete implementation, lazy-loaded)
- SpaCyNERDetector (concrete implementation, lazy-loaded)
- QwenPIIClassifier (auxiliary classifier, lazy-loaded)

Important:
- Importing this package must not require optional NLP / model dependencies such
  as ``presidio_analyzer``, downloaded spaCy models, or the ``ollama`` Python
  package. This keeps the PIIDetector ABC independently testable and matches
  NETWORK_ENGINEERING_DESIGN.md §12.1 (module-isolated unit tests).
"""

from __future__ import annotations

from .base import PIIDetector

__all__ = ["PIIDetector", "PresidioDetector", "QwenPIIClassifier", "SpaCyNERDetector"]


def __getattr__(name: str):
    """Lazy-load optional concrete detectors/classifiers only when requested."""
    if name == "PresidioDetector":
        from .presidio_detector import PresidioDetector

        return PresidioDetector
    if name == "SpaCyNERDetector":
        from .ner_detector import SpaCyNERDetector

        return SpaCyNERDetector
    if name == "QwenPIIClassifier":
        from .qwen_classifier import QwenPIIClassifier

        return QwenPIIClassifier
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

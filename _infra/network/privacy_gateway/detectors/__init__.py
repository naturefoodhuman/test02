# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 19:32:46

"""
Detectors subpackage for Privacy Gateway (E5-C3).

Exports:
- PIIDetector (ABC)
- PresidioDetector (concrete implementation, lazy-loaded)

Important:
- Importing this package must not require optional NLP dependencies such as
  ``presidio_analyzer``. This keeps the PIIDetector ABC independently testable
  and matches NETWORK_ENGINEERING_DESIGN.md §12.1 (module-isolated unit tests).
"""

from __future__ import annotations

from .base import PIIDetector

__all__ = ["PIIDetector", "PresidioDetector"]


def __getattr__(name: str):
    """Lazy-load optional concrete detectors only when requested."""
    if name == "PresidioDetector":
        from .presidio_detector import PresidioDetector

        return PresidioDetector
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

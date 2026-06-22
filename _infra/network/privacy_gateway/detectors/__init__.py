"""
Detectors subpackage for Privacy Gateway (E5-C3).

Exports:
- PIIDetector (ABC)
- PresidioDetector (concrete implementation)
"""

from .base import PIIDetector
from .presidio_detector import PresidioDetector

__all__ = ["PIIDetector", "PresidioDetector"]

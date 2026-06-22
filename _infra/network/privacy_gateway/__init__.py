"""
Privacy Gateway module (FORGE Network incremental)

M-07: 7-layer PII detection pipeline

Core exports:
- PIIType, PIIEntity (models)
- PIIDetector (ABC) — import from .detectors.base for concrete use
"""

from .models import PIIType, PIIEntity

# Note: PIIDetector is intentionally not imported at top level to avoid
# circular dependencies during early development.
# Recommended usage:
#   from _infra.network.privacy_gateway.detectors.base import PIIDetector
#   from _infra.network.privacy_gateway import PIIType, PIIEntity

__all__ = [
    "PIIEntity",
    "PIIType",
]

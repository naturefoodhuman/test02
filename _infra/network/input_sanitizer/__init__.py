"""
Input Sanitizer module (FORGE Network incremental)

M-06: HTML stripping, prompt injection detection, provenance marking.

Exports:
- InputSanitizer
- sanitize()
"""

from .sanitizer import InputSanitizer, sanitize, SanitizedContent

__all__ = [
    "InputSanitizer",
    "sanitize",
    "SanitizedContent",
]

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""FEOS exception hierarchy."""

from __future__ import annotations


class FEOSError(Exception):
    """Base FEOS error."""


class FEOSConfigError(FEOSError):
    """Configuration loading or validation failed."""


class FEOSStateError(FEOSError):
    """Invalid case state or transition."""


class FEOSStorageError(FEOSError):
    """Local storage operation failed."""


class FEOSPolicyError(FEOSError):
    """Policy plane rejected an operation."""


class FEOSVerificationError(FEOSError):
    """Verification failed or cannot proceed."""

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 19:32:46

"""
PIIDetector abstract base class

Per TASK_BACKLOG E5-C3-S1-T1 + NETWORK_ENGINEERING_DESIGN §5.3 / §5.4

Defines the contract for all PII detectors in the Privacy Gateway pipeline.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..models import PIIEntity


class PIIDetector(ABC):
    """
    Abstract base class for PII detectors.

    职责：
    - 接收原始文本（应已通过 Unicode 规范化 + InputSanitizer）
    - 返回检测到的 PIIEntity 列表
    - 生命周期：无状态，可复用
    """

    @abstractmethod
    async def detect(self, text: str) -> List[PIIEntity]:
        """
        Detect PII entities in the given text.

        Returns:
            List of PIIEntity (sorted by start offset recommended).
        """
        ...

    def get_name(self) -> str:
        """Human / log friendly detector name."""
        return self.__class__.__name__.replace("Detector", "").lower()

    async def health_check(self) -> bool:
        """Optional health check. Default: always healthy."""
        return True

    def supports_type(self, pii_type: "PIIType") -> bool:
        """Default: supports all types."""
        return True


__all__ = ["PIIDetector"]

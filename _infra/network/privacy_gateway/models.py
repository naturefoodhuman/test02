# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 19:32:46

"""
Privacy models (PII detection)

Per TASK_BACKLOG E5-C3-S1-T1 + NETWORK_ENGINEERING_DESIGN §5.4

Defines:
- PIIType (Enum)
- PIIEntity (Pydantic model)
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class PIIType(str, Enum):
    """Supported PII entity types (including Chinese)."""

    # Common international
    EMAIL_ADDRESS = "EMAIL_ADDRESS"
    PHONE_NUMBER = "PHONE_NUMBER"
    CREDIT_CARD = "CREDIT_CARD"
    IP_ADDRESS = "IP_ADDRESS"
    PERSON = "PERSON"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"

    # Chinese specific (will be used by custom recognizers)
    CN_PHONE = "CN_PHONE"           # 11-digit Chinese mobile
    CN_ID_CARD = "CN_ID_CARD"       # 18-digit ID card
    CN_NAME = "CN_NAME"
    CN_ADDRESS = "CN_ADDRESS"
    BANK_CARD = "BANK_CARD"

    # Secrets / tokens (very high risk)
    API_KEY = "API_KEY"
    ACCESS_TOKEN = "ACCESS_TOKEN"
    JWT = "JWT"
    PRIVATE_KEY = "PRIVATE_KEY"


class PIIEntity(BaseModel):
    """
    Detected PII entity.

    start / end are character offsets in the original text.
    """

    type: PIIType
    value: str = Field(..., min_length=1)
    start: int = Field(..., ge=0)
    end: int = Field(..., ge=0)
    score: float = Field(0.95, ge=0.0, le=1.0)
    recognizer: str = "unknown"   # e.g. "presidio", "cn_phone", "spacy"

    @property
    def length(self) -> int:
        return self.end - self.start

    def mask(self, mask_char: str = "*") -> str:
        """Return a masked version of the value (for logging)."""
        if len(self.value) <= 4:
            return mask_char * len(self.value)
        return self.value[:2] + mask_char * (len(self.value) - 4) + self.value[-2:]

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
    }

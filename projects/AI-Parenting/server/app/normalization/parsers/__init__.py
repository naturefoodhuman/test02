# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-13 00:00:00
"""Normalization parsers（APC-T013）。

- ``form``：manual 表单解析（normalized_payload 已结构化，confidence=1.0）。
- ``voice``：voice_text 语音文本解析（规则/模板，confidence < 1.0；LLM 在 T027+ 接入）。
"""

from .form import parse_form
from .voice import parse_voice

__all__ = ["parse_form", "parse_voice"]

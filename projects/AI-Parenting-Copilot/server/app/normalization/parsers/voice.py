# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 22:20:00

"""Voice/text parser for P0 record types.

This remains a deterministic P0 parser. Production-grade NLU is intentionally left to
Logger Copilot/Model Gateway fallback, but common Chinese word orders are covered here.
"""

from __future__ import annotations

import re

FEEDING_PATTERNS = [
    re.compile(r"(?:喂|喝|奶).*?(?P<amount>\d+(?:\.\d+)?)\s*(?:ml|毫升)", re.I),
    re.compile(r"(?P<amount>\d+(?:\.\d+)?)\s*(?:ml|毫升).*?(?:奶)", re.I),
]
TEMP_RE = re.compile(r"(?P<temp>\d{1,3}(?:\.\d+)?)\s*(?:度|℃|c)", re.I)


def parse_voice_text(text: str) -> tuple[str, dict[str, object], float]:
    for pattern in FEEDING_PATTERNS:
        feeding = pattern.search(text)
        if feeding:
            return "feeding", {"amount_ml": float(feeding.group("amount"))}, 0.88
    temp = TEMP_RE.search(text)
    if temp:
        return "temperature", {"value_c": float(temp.group("temp"))}, 0.85
    if re.search(r"尿布|纸尿裤|便便|大便|尿", text):
        return "diaper", {"note": text, "diaper_type": "unknown"}, 0.75
    if re.search(r"睡|醒|入睡", text):
        return "sleep", {"note": text}, 0.70
    return "unknown", {"raw_text": text}, 0.2

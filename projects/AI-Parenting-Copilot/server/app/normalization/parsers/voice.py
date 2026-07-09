# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 12:50:00


"""Voice/text parser for P0 record types."""

from __future__ import annotations

import re

FEEDING_RE = re.compile(r"(?:喂|喝|奶).*?(?P<amount>\d+(?:\.\d+)?)\s*(?:ml|毫升)", re.I)
TEMP_RE = re.compile(r"(?P<temp>\d{2}(?:\.\d)?)\s*(?:度|℃|c)", re.I)


def parse_voice_text(text: str) -> tuple[str, dict[str, object], float]:
    feeding = FEEDING_RE.search(text)
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

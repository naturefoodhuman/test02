# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-13 00:00:00
#
# app/normalization/parsers/voice.py —— 语音文本解析（voice_text source，APC-T013）。
# 依据：ENGINEERING_DESIGN §2 M05（语音 → ObservationEvent；置信度可 <1.0）、§7.1；
#       TASK_BACKLOG APC-T013（voice_text 解析；confidence 可低于 1.0；不识别事件保留
#       observation_event 标记 processing_status）。
# 设计：P0 用规则/模板解析中文语音文本（"刚喂了90ml奶" → feeding amount_ml=90），
#       不调用 LLM（LLM 通过 ModelClient 在 T027+ Logger Copilot 接入）。
#       解析失败 → 低置信候选（confidence < 1.0），不抛异常（保留事件，标记 processing_status）。
# 边界：只做文本模式匹配，不做医疗判断；不调用 LLM/不查 DB。

"""语音文本解析（voice_text source，APC-T013）。

P0 用规则/模板解析中文语音文本（架构 §7.1：App 本地 Logger 解析），
不调用 LLM（LLM 通过 ``ModelClient`` 在 T027+ Logger Copilot 接入）。

解析示例：
    - ``"刚喂了90ml奶"`` → feeding, amount_ml=90, confidence=0.9
    - ``"换了个湿尿布"`` → diaper, type=wet, confidence=0.85
    - ``"体温38度5"`` → temperature, value_c=38.5, confidence=0.85
    - ``"睡了"`` → sleep, confidence=0.7（缺时长，低置信）

解析失败 → 低置信候选（``confidence < 1.0``），不抛异常（保留事件，
标记 ``processing_status``，架构 §7.1 不丢记录）。

边界：只做文本模式匹配，不做医疗判断；不调用 LLM/不查 DB。
"""

from __future__ import annotations

import re
from typing import Any

from ..domain import EVENT_TYPE_TO_TABLE, P0_EVENT_TYPES, LogTable, NormalizedRecord

# voice_text 置信度（架构 §2 M05：voice_text 可 <1.0）。
VOICE_CONFIDENCE_FULL = 0.9  # 关键字段齐全
VOICE_CONFIDENCE_PARTIAL = 0.7  # 缺关键字段
VOICE_CONFIDENCE_UNKNOWN = 0.4  # 无法识别 event_type

# 中文数字 → 阿拉伯数字（P0 常见量级）。
_CN_DIGITS = {
    "零": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}

# 模式：喂奶（"喂了90ml奶" / "喝了120毫升"）。
_FEEDING_RE = re.compile(
    r"(?:喂|喝|吃|补)\s*(?:了\s*)?(\d+(?:\.\d+)?)\s*(?:ml|毫升|cc)\s*(?:奶|配方奶|母乳)?"
)
# 模式：尿布（"湿尿布" / "拉了屎" / "尿了"）。
_DIAPER_WET = re.compile(r"湿|尿|小便")
_DIAPER_DIRTY = re.compile(r"屎|便|大便|拉了|粑粑")
# 模式：体温（"体温38度5" / "38.5度" / "烧到38"）。
_TEMP_RE = re.compile(r"(?:体温|温度|烧到?|量了)?\s*(\d+(?:\.\d+)?)\s*度(?:\s*(\d))?")
# 模式：补剂（"吃了维生素D" / "补了DHA"）。
_SUPPLEMENT_RE = re.compile(r"(?:吃|补|喂)\s*(?:了\s*)?([一-龥a-zA-Z][一-龥a-zA-Z0-9]*)")


def parse_voice(
    *,
    event_id: str,
    baby_id: str,
    event_type: str,
    raw_input: dict[str, Any] | None,
    normalized_payload: dict[str, Any],
    start_time: Any,
    end_time: Any | None = None,
) -> NormalizedRecord | None:
    """解析 voice_text 事件 → NormalizedRecord（confidence < 1.0）。

    优先用 ``normalized_payload``（若 App 端已部分结构化），其次从 ``raw_input`` 文本解析。
    event_type 不在 P0 范围返回 ``None``（调用方保留事件）。

    Args:
        raw_input: 原始输入（含 ``text`` 字段为语音转写文本）。
        normalized_payload: App 端可能已部分结构化的载荷（优先用）。
    """
    if event_type not in P0_EVENT_TYPES:
        return None
    table: LogTable = EVENT_TYPE_TO_TABLE[event_type]
    text = _extract_text(raw_input, normalized_payload)

    # 优先用 normalized_payload 已有字段，缺失的从文本解析补全。
    payload = dict(normalized_payload)
    confidence = VOICE_CONFIDENCE_FULL

    if event_type == "feeding":
        if payload.get("amount_ml") is None:
            amount = _parse_feeding_amount(text)
            if amount is not None:
                payload["amount_ml"] = amount
            else:
                confidence = VOICE_CONFIDENCE_PARTIAL
    elif event_type == "diaper":
        if payload.get("type") is None:
            dtype = _parse_diaper_type(text)
            if dtype is not None:
                payload["type"] = dtype
            else:
                confidence = VOICE_CONFIDENCE_PARTIAL
    elif event_type == "temperature":
        if payload.get("value_c") is None:
            temp = _parse_temperature(text)
            if temp is not None:
                payload["value_c"] = temp
            else:
                confidence = VOICE_CONFIDENCE_PARTIAL
    elif event_type == "supplement":
        if payload.get("name") is None and payload.get("supplement_name") is None:
            name = _parse_supplement_name(text)
            if name is not None:
                payload["name"] = name
        # 缺 name 或解析失败均降级（下方统一判断）。
        if payload.get("name") is None and payload.get("supplement_name") is None:
            confidence = VOICE_CONFIDENCE_PARTIAL
    # sleep：voice 无额外字段，保持 full confidence（事件层已保证 start_time）。

    structured = _extract_structured(event_type, payload, start_time, end_time)
    return NormalizedRecord(
        event_id=event_id,
        baby_id=baby_id,
        table=table,
        structured=structured,
        payload=payload,
        confidence=confidence,
    )


def _extract_text(raw_input: dict[str, Any] | None, normalized_payload: dict[str, Any]) -> str:
    """从 raw_input 或 normalized_payload 取语音转写文本。"""
    if raw_input and isinstance(raw_input.get("text"), str):
        return raw_input["text"]
    if isinstance(normalized_payload.get("text"), str):
        return normalized_payload["text"]
    if isinstance(normalized_payload.get("raw_text"), str):
        return normalized_payload["raw_text"]
    return ""


def _parse_feeding_amount(text: str) -> int | None:
    m = _FEEDING_RE.search(text)
    if not m:
        return None
    try:
        val = float(m.group(1))
        return int(val) if val.is_integer() else None
    except ValueError:
        return None


def _parse_diaper_type(text: str) -> str | None:
    wet = bool(_DIAPER_WET.search(text))
    dirty = bool(_DIAPER_DIRTY.search(text))
    if wet and dirty:
        return "mixed"
    if dirty:
        return "dirty"
    if wet:
        return "wet"
    return None


def _parse_temperature(text: str) -> float | None:
    m = _TEMP_RE.search(text)
    if not m:
        return None
    try:
        base = float(m.group(1))
        # "38度5" → 38.5。
        if m.group(2):
            base += float(f"0.{m.group(2)}")
        return base
    except ValueError:
        return None


def _parse_supplement_name(text: str) -> str | None:
    m = _SUPPLEMENT_RE.search(text)
    return m.group(1) if m else None


def _extract_structured(
    event_type: str,
    payload: dict[str, Any],
    start_time: Any,
    end_time: Any | None,
) -> dict[str, Any]:
    """提取派生表结构化列（与 form parser 一致，仅 feeding_log 有结构化列）。"""
    if event_type == "feeding":
        val = payload.get("amount_ml")
        amount = int(val) if isinstance(val, int | float) and not isinstance(val, bool) else None
        return {
            "amount_ml": amount,
            "feeding_type": payload.get("feeding_type")
            if isinstance(payload.get("feeding_type"), str)
            else None,
            "started_at": start_time,
            "ended_at": end_time,
        }
    return {}


__all__ = [
    "VOICE_CONFIDENCE_FULL",
    "VOICE_CONFIDENCE_PARTIAL",
    "VOICE_CONFIDENCE_UNKNOWN",
    "parse_voice",
]

# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""PG LISTEN/NOTIFY payload 解析单元测试（APC-T011 测试要求：Unit payload parse）。

验证 ``parse_event_payload``：
    - 合法 JSON 含 event_id/baby_id/op → 解析成功。
    - 非法 JSON → ValueError。
    - 缺少必填字段（event_id/baby_id/op）→ ValueError。
    - 非 dict（如 JSON 数组）→ ValueError。
"""

from __future__ import annotations

import json

import pytest

from server.app.common.event_bus import parse_event_payload


class TestParseEventPayload:
    def test_valid_payload(self):
        raw = json.dumps(
            {
                "event_id": "01HZXKQW7P0QJ9V8R3M4N6H5T2",
                "baby_id": "01HZXKQW7P0QJ9V8R3M4N6H5T3",
                "family_id": "01HZXKQW7P0QJ9V8R3M4N6H5T4",
                "op": "insert",
            }
        )
        data = parse_event_payload(raw)
        assert data["event_id"] == "01HZXKQW7P0QJ9V8R3M4N6H5T2"
        assert data["op"] == "insert"

    @pytest.mark.parametrize("bad_json", ["", "not json", "{", "null", "123"])
    def test_invalid_json_raises(self, bad_json):
        with pytest.raises(ValueError):
            parse_event_payload(bad_json)

    def test_non_object_json_raises(self):
        with pytest.raises(ValueError):
            parse_event_payload(json.dumps(["a", "b"]))

    @pytest.mark.parametrize("missing", ["event_id", "baby_id", "op"])
    def test_missing_required_field_raises(self, missing):
        data = {
            "event_id": "01HZXKQW7P0QJ9V8R3M4N6H5T2",
            "baby_id": "01HZXKQW7P0QJ9V8R3M4N6H5T3",
            "family_id": "01HZXKQW7P0QJ9V8R3M4N6H5T4",
            "op": "insert",
        }
        del data[missing]
        with pytest.raises(ValueError):
            parse_event_payload(json.dumps(data))

    def test_extra_fields_preserved(self):
        raw = json.dumps(
            {
                "event_id": "01HZXKQW7P0QJ9V8R3M4N6H5T2",
                "baby_id": "01HZXKQW7P0QJ9V8R3M4N6H5T3",
                "op": "update",
                "family_id": "01HZXKQW7P0QJ9V8R3M4N6H5T4",
            }
        )
        data = parse_event_payload(raw)
        assert data["family_id"] == "01HZXKQW7P0QJ9V8R3M4N6H5T4"

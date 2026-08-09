# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
"""ULID 生成单元测试（APC-T002 测试要求：ULID 格式）。"""

from __future__ import annotations

from server.app.common.ids import is_valid_ulid, new_id, parse_ulid


def test_new_id_is_26_char_ulid():
    for _ in range(100):
        u = new_id()
        assert len(u) == 26
        assert is_valid_ulid(u)


def test_new_ids_are_time_ordered():
    """ULID 时间有序：同毫秒内单调递增，跨毫秒严格递增。"""
    ids = [new_id() for _ in range(50)]
    assert ids == sorted(ids)


def test_new_ids_are_unique():
    ids = {new_id() for _ in range(1000)}
    assert len(ids) == 1000


def test_is_valid_ulid_rejects_invalid():
    assert not is_valid_ulid("")
    assert not is_valid_ulid("not-a-ulid")
    assert not is_valid_ulid("0" * 25)  # 长度不足
    # 首字符必须 [0-7]；'8' 非法
    assert not is_valid_ulid("8" + "0" * 25)
    # 含非法字符 I/L/O/U
    assert not is_valid_ulid("0" + "I" * 25)


def test_parse_ulid_returns_object_with_timestamp():
    u = new_id()
    parsed = parse_ulid(u)
    assert str(parsed) == u
    # datetime 为 timezone-aware UTC
    ts = parsed.datetime
    assert ts.tzinfo is not None

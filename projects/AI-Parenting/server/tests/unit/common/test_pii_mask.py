# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""PII 脱敏单元测试（APC-T005 测试要求：Unit PII mask）。

覆盖 logger.mask_pii：敏感 key 整体替换、手机号/邮箱/身份证正则脱敏、
媒体路径文件名脱敏、dict/list/tuple 递归、非 str 原样返回。
"""

from __future__ import annotations

from server.app.observability.logger import bind_context, clear_context, get_context, mask_pii


def test_sensitive_keys_masked_to_stars():
    """命中 _SENSITIVE_KEYS 的 value 整体替换为 '***'，不递归内容。"""
    payload = {
        "raw_input": "宝宝今早发烧 38.5 度，电话 13800138000",
        "password": "s3cret",
        "token": "eyJhbGciOiJIUzI1",
        "fcm_token": "abc123",
        "normal_field": "保留原值",
    }
    out = mask_pii(payload)
    assert out["raw_input"] == "***"
    assert out["password"] == "***"
    assert out["token"] == "***"
    assert out["fcm_token"] == "***"
    assert out["normal_field"] == "保留原值"


def test_phone_email_id_card_patterns_masked():
    """手机号/邮箱/身份证正则命中即替换为 '***'。"""
    text = "联系 13800138000 或 alice@example.com，身份证 110101199003077834"
    out = mask_pii(text)
    assert "13800138000" not in out
    assert "alice@example.com" not in out
    assert "110101199003077834" not in out
    assert "***" in out


def test_media_path_filename_masked():
    """媒体路径保留目录结构，文件名脱敏为 '***'。"""
    path = "/data/media/2026/08/voice_宝宝哭声.m4a"
    out = mask_pii(path)
    assert out == "/data/media/2026/08/***"


def test_recursive_dict_list_tuple():
    """dict / list / tuple 递归脱敏。"""
    payload = {
        "events": [
            {"raw_input": "敏感", "note": "电话 13900139000"},
            {"raw": "也脱敏"},
        ],
        "meta": ("token", "电话 13900139000"),
    }
    out = mask_pii(payload)
    assert out["events"][0]["raw_input"] == "***"
    assert "13900139000" not in out["events"][0]["note"]
    assert out["events"][1]["raw"] == "***"
    # tuple 是位置序列（非 key-value），按元素递归跑 PII 正则；
    # "token" 字符串本身不匹配任何 PII 模式故原样，第二元素手机号被脱敏。
    assert out["meta"][0] == "token"
    assert "13900139000" not in out["meta"][1]
    assert "***" in out["meta"][1]


def test_non_string_values_passthrough():
    """int/float/bool/None 原样返回（不脱敏）。"""
    assert mask_pii(42) == 42
    assert mask_pii(3.14) == 3.14
    assert mask_pii(True) is True
    assert mask_pii(None) is None


def test_bind_context_masks_pii():
    """bind_context 注入的 PII 经脱敏后再绑定，不泄漏到日志上下文。"""
    try:
        bind_context(
            trace_id="01J00000000000000000000000",
            request_id="01J00000000000000000000001",
            raw_input="宝宝发烧 38.5 电话 13800138000",
        )
        ctx = get_context()
        assert ctx["trace_id"] == "01J00000000000000000000000"
        assert ctx["request_id"] == "01J00000000000000000000001"
        # raw_input 被脱敏为 ***
        assert ctx["raw_input"] == "***"
        assert "13800138000" not in str(ctx)
    finally:
        clear_context()


def test_clear_context_resets():
    """clear_context 清理后上下文为空，防止跨请求泄漏。"""
    bind_context(trace_id="01J00000000000000000000002")
    clear_context()
    assert get_context() == {}

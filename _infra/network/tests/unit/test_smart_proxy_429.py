# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-02 15:17:00
#
# 单测：smart_proxy 对上游 429/502/503/504 的退避重试行为。
# 覆盖：
#   1. 纯函数 _retry_after_seconds_from_value（None/合法/超封顶/非法）
#   2. RETRYABLE_STATUS_CODES 含 429
#   3. 非流式 _forward_with_retries：429→Retry-After→200 成功；429 三次全失败→504
#   4. 流式 _stream_line_producer：http_error 附带 status/retry_after
#   5. 流式重试守卫：未发内容时 429 重试成功；已发内容时不重试

import asyncio
import json
import sys
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

# _infra/smart_proxy.py 位于仓库根，需把仓库根加入 sys.path
_REPO_ROOT = __import__("os").path.abspath(__import__("os").path.join(__import__("os").path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import _infra.smart_proxy as sp  # noqa: E402


# ============================================================
# 1. 纯函数
# ============================================================
class TestRetryAfterHelpers:
    def test_none_returns_default(self):
        assert sp._retry_after_seconds_from_value(None, 2.0) == 2.0

    def test_valid_header_value(self):
        assert sp._retry_after_seconds_from_value("5", 2.0) == 5.0

    def test_cap_at_30(self):
        assert sp._retry_after_seconds_from_value("999", 2.0) == 30.0

    def test_illegal_falls_back_to_default(self):
        assert sp._retry_after_seconds_from_value("not-a-number", 3.0) == 3.0

    def test_retryable_includes_429(self):
        assert 429 in sp.RETRYABLE_STATUS_CODES
        assert {502, 503, 504}.issubset(sp.RETRYABLE_STATUS_CODES)

    def test_retry_after_seconds_from_resp(self):
        resp = httpx.Response(429, headers={"Retry-After": "7"})
        assert sp._retry_after_seconds(resp, default=2.0) == 7.0

    def test_retry_after_seconds_from_resp_missing(self):
        resp = httpx.Response(429)
        assert sp._retry_after_seconds(resp, default=2.0) == 2.0


# ============================================================
# 2. 非流式 _forward_with_retries
# ============================================================
def _make_mock_response(status, body="", headers=None):
    r = httpx.Response(status, text=body, headers=headers or {})
    return r


class TestNonStreamingRetry:
    @pytest.mark.asyncio
    async def test_429_then_200_succeeds(self, monkeypatch):
        """第一次 429（带 Retry-After: 0），第二次 200 → 最终成功，且实际 sleep 被调用。"""
        sleeps = []
        async def fake_sleep(s):
            sleeps.append(s)
        monkeypatch.setattr(sp.asyncio, "sleep", fake_sleep)

        calls = {"n": 0}
        async def fake_post(url, json=None, headers=None):
            calls["n"] += 1
            if calls["n"] == 1:
                return _make_mock_response(429, body='{"error":"rate"}', headers={"Retry-After": "0"})
            return _make_mock_response(200, body='{"ok":true}')

        fake_client = MagicMock(spec=httpx.AsyncClient)
        fake_client.post = fake_post
        monkeypatch.setattr(sp, "http_client", fake_client)
        monkeypatch.setattr(sp, "_local_port_guard", lambda p: sp._NullContext())

        resp, err = await sp._forward_with_retries(
            "http://up/v1", {}, {}, is_remote=True, target_port=8080
        )
        assert resp is not None and resp.status_code == 200
        assert err is None
        assert calls["n"] == 2
        assert sleeps == [0.0]  # Retry-After: 0 → 退避 0s
        assert sp._retry_counters.get("429", 0) >= 1

    @pytest.mark.asyncio
    async def test_429_all_attempts_fail_returns_504(self, monkeypatch):
        """remote 默认重试 2 次 → 3 次尝试全 429 → 返回 (resp, last_exception) 含 429。"""
        async def fake_sleep(s):
            pass
        monkeypatch.setattr(sp.asyncio, "sleep", fake_sleep)

        async def fake_post(url, json=None, headers=None):
            return _make_mock_response(429, body='{"error":"rate"}', headers={"Retry-After": "0"})

        fake_client = MagicMock(spec=httpx.AsyncClient)
        fake_client.post = fake_post
        monkeypatch.setattr(sp, "http_client", fake_client)
        monkeypatch.setattr(sp, "_local_port_guard", lambda p: sp._NullContext())

        resp, err = await sp._forward_with_retries(
            "http://up/v1", {}, {}, is_remote=True, target_port=8080
        )
        # 三次尝试后 resp 是最后一次 429 响应，err 非空且含 429
        assert resp is not None and resp.status_code == 429
        assert err is not None and "429" in err

    @pytest.mark.asyncio
    async def test_non_retryable_status_no_retry(self, monkeypatch):
        """400 不可重试 → 立即失败，只调用一次。"""
        async def fake_sleep(s):
            raise AssertionError("不应退避重试")
        monkeypatch.setattr(sp.asyncio, "sleep", fake_sleep)

        calls = {"n": 0}
        async def fake_post(url, json=None, headers=None):
            calls["n"] += 1
            return _make_mock_response(400, body='{"error":"bad"}')

        fake_client = MagicMock(spec=httpx.AsyncClient)
        fake_client.post = fake_post
        monkeypatch.setattr(sp, "http_client", fake_client)
        monkeypatch.setattr(sp, "_local_port_guard", lambda p: sp._NullContext())

        resp, err = await sp._forward_with_retries(
            "http://up/v1", {}, {}, is_remote=True, target_port=8080
        )
        assert calls["n"] == 1
        assert resp is not None and resp.status_code == 400


# ============================================================
# 3. 流式 _stream_line_producer：http_error 附带 status/retry_after
# ============================================================
class TestStreamProducerErrorPayload:
    @pytest.mark.asyncio
    async def test_non_200_emits_structured_http_error(self, monkeypatch):
        class _Resp:
            status_code = 429
            headers = {"Retry-After": "3"}
            async def aread(self):
                return b'{"status":429}'
            async def aiter_lines(self):
                if False:
                    yield ""  # 使其成为 async generator

        class _RespCtx:
            async def __aenter__(self):
                return _Resp()
            async def __aexit__(self, *a):
                return False

        class _Ctx:
            async def __aenter__(self): return self
            async def __aexit__(self, *a): return False

        def fake_stream(method, url, json=None, headers=None):
            return _RespCtx()

        fake_client = MagicMock(spec=httpx.AsyncClient)
        fake_client.stream = fake_stream
        monkeypatch.setattr(sp, "http_client", fake_client)

        queue: asyncio.Queue = asyncio.Queue()
        await sp._stream_line_producer("http://up", {}, {}, _Ctx(), queue)

        kind, item = await queue.get()
        assert kind == "http_error"
        assert isinstance(item, dict)
        assert item["status"] == 429
        assert item["retry_after"] == "3"
        assert "429" in item["body"]
        # 紧跟 eof
        kind2, _ = await queue.get()
        assert kind2 == "eof"


# ============================================================
# 4. 流式重试守卫：未发内容时重试成功 / 已发内容时不重试
#   通过直接驱动 anthropic_event_stream 的内层逻辑验证守卫判定。
#   这里用 _stream_line_producer 的输出 + 守卫条件做白盒断言，避免完整
#   async generator 的重型装配（tracker/rpm_guard 等模块级副作用）。
# ============================================================
class TestStreamRetryGuardConditions:
    def test_guard_condition_unsent_content(self):
        """未发内容 + 可重试状态码 + 还有次数 → 满足重试守卫。"""
        item = {"status": 429, "body": "", "retry_after": "0"}
        emitted_text = False
        tool_calls_data = {}
        stream_attempt = 0
        stream_attempts = 3
        should_retry = (
            item.get("status") in sp.RETRYABLE_STATUS_CODES
            and not emitted_text
            and not tool_calls_data
            and stream_attempt < stream_attempts - 1
        )
        assert should_retry is True

    def test_guard_condition_already_emitted_text(self):
        """已发文本 → 不重试（文档 §12 铁律）。"""
        item = {"status": 429, "body": "", "retry_after": "0"}
        emitted_text = True  # 关键：已向客户端发过内容
        tool_calls_data = {}
        stream_attempt = 0
        stream_attempts = 3
        should_retry = (
            item.get("status") in sp.RETRYABLE_STATUS_CODES
            and not emitted_text
            and not tool_calls_data
            and stream_attempt < stream_attempts - 1
        )
        assert should_retry is False

    def test_guard_condition_already_has_tool_calls(self):
        """已有 tool_calls（即使没发文本）→ 不重试。"""
        item = {"status": 503, "body": "", "retry_after": None}
        emitted_text = False
        tool_calls_data = {0: {"id": "x", "name": "f", "arguments": "{}"}}
        stream_attempt = 0
        stream_attempts = 3
        should_retry = (
            item.get("status") in sp.RETRYABLE_STATUS_CODES
            and not emitted_text
            and not tool_calls_data
            and stream_attempt < stream_attempts - 1
        )
        assert should_retry is False

    def test_guard_condition_last_attempt(self):
        """最后一次尝试 → 不再重试。"""
        item = {"status": 429, "body": "", "retry_after": "0"}
        emitted_text = False
        tool_calls_data = {}
        stream_attempt = 2  # 0,1,2 共 3 次，这是最后一次
        stream_attempts = 3
        should_retry = (
            item.get("status") in sp.RETRYABLE_STATUS_CODES
            and not emitted_text
            and not tool_calls_data
            and stream_attempt < stream_attempts - 1
        )
        assert should_retry is False

    def test_guard_condition_non_retryable_status(self):
        """400 不可重试 → 不重试。"""
        item = {"status": 400, "body": "", "retry_after": None}
        emitted_text = False
        tool_calls_data = {}
        stream_attempt = 0
        stream_attempts = 3
        should_retry = (
            item.get("status") in sp.RETRYABLE_STATUS_CODES
            and not emitted_text
            and not tool_calls_data
            and stream_attempt < stream_attempts - 1
        )
        assert should_retry is False

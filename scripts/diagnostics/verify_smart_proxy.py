"""
scripts/diagnostics/verify_smart_proxy.py

对应交接文档 §20 + §21 的 "live"（黑盒集成）验收测试。

运行前提：
  - _infra/smart_proxy.py 已通过 scripts/forge-start.sh 或
    `python3 _infra/smart_proxy.py` 实际监听在 FORGE_TEST_BASE_URL
    （默认 http://127.0.0.1:4000）。
  - 依赖真实模型行为的用例（工具调用、流式、冷暖缓存）需要本地 MTPLX 8080
    能被代理按需拉起。test_remote_full_forward 例外：它通过 ASGI in-process
    + mock 后端自包含运行，不需要真实运行中的 4000 进程或远程 API Key
    （文档 §20.5 原文允许 "mock/unit test"）。

运行方式：
    pytest scripts/diagnostics/verify_smart_proxy.py -v
    # 或
    python3 scripts/diagnostics/verify_smart_proxy.py

环境变量：
    FORGE_TEST_BASE_URL   默认 http://127.0.0.1:4000
    FORGE_TEST_LOCAL_MODEL 默认 claude-haiku-4-5
    RUN_SLOW=1            启用 test_warm_cold_cache（涉及分钟级冷 prefill）
    RUN_HOOK_TEST=1       启用 test_feishu_hook_timeout

覆盖关系（对应交接文档 §21 表格）：
    test_static_checks                     -> §20.1
    test_health                            -> §20.2
    test_count_tokens_circuit_breaker      -> §20.3
    test_local_tool_limit                  -> §20.4（数量部分；深度相等见 unit 测试）
    test_remote_full_forward               -> §20.5（自包含 mock 后端）
    test_forced_tool_choice                -> §20.6
    test_tool_result_turn                  -> §20.7
    test_streaming_text_and_ping           -> §20.9
    test_streaming_tool_call               -> §20.10
    test_usage_never_zero                  -> §20.11
    test_warm_cold_cache                   -> §20.12（默认跳过，需 RUN_SLOW=1）
    test_unknown_model_rejected            -> 新增（§3.3）
    test_tool_choice_none                  -> 新增（§9.5，依赖本文档给出的 smart_proxy.py 补丁）
    test_client_disconnect_cancels_backend -> 新增
    test_feishu_hook_timeout               -> §20.15（可选，需 RUN_HOOK_TEST=1）
    §20.13 SSD 重启恢复                     -> 见 verify_ssd_session_cache.py（destructive）
    §20.14 真实 Claude Code                 -> 见文件末尾 MANUAL_CHECKLIST_20_14（人工步骤）
"""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

BASE_URL = os.getenv("FORGE_TEST_BASE_URL", "http://127.0.0.1:4000")
LOCAL_MODEL = os.getenv("FORGE_TEST_LOCAL_MODEL", "claude-haiku-4-5")
UNKNOWN_MODEL = "definitely-not-a-real-model-xyz"
RUN_SLOW = os.getenv("RUN_SLOW", "0") == "1"
RUN_HOOK_TEST = os.getenv("RUN_HOOK_TEST", "0") == "1"
PING_INTERVAL = float(os.getenv("FORGE_STREAM_PING_INTERVAL_SECONDS", "10"))


def _proxy_reachable():
    try:
        r = httpx.get(f"{BASE_URL}/_forge/health", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


PROXY_UP = _proxy_reachable()
skip_no_proxy = pytest.mark.skipif(
    not PROXY_UP, reason=f"smart_proxy 未在 {BASE_URL} 监听，跳过 live 测试"
)


def _is_port_listening(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _make_synthetic_tools(n=25):
    tools = []
    for i in range(n):
        tools.append({
            "name": f"Tool{i:02d}",
            "description": (f"Synthetic tool #{i} used for verification only. " * 3),
            "input_schema": {
                "type": "object",
                "properties": {
                    "arg1": {"type": "string", "description": f"arg for Tool{i:02d}"},
                    "arg2": {"type": "integer"},
                },
                "required": ["arg1"],
            },
        })
    return tools


def _weather_tool():
    return {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }


def _get_status():
    r = httpx.get(f"{BASE_URL}/_forge/status", timeout=5.0)
    r.raise_for_status()
    return r.json()


# ------------------------------------------------------------------
# §20.1 静态检查
# ------------------------------------------------------------------
def test_static_checks():
    r1 = subprocess.run(
        [sys.executable, "-m", "py_compile", str(ROOT / "_infra" / "smart_proxy.py")],
        capture_output=True, text=True,
    )
    assert r1.returncode == 0, r1.stderr

    r2 = subprocess.run(
        [sys.executable, "-m", "py_compile", str(ROOT / "_infra" / "model_runtime.py")],
        capture_output=True, text=True,
    )
    assert r2.returncode == 0, r2.stderr

    r3 = subprocess.run(
        [sys.executable, str(ROOT / "_infra" / "model_runtime.py"), "command", "8080"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert r3.returncode == 0, r3.stderr
    cmd = r3.stdout.strip()
    assert "--ssd-session-cache" in cmd
    assert "--ssd-session-cache-dir" in cmd
    assert "${HOME}" not in cmd, "路径未展开，_expand() 递归展开可能失效（文档 §14.4）"
    assert "2048" in cmd, "本地 max-tokens 应为 2048"


# ------------------------------------------------------------------
# §20.2 健康检查
# ------------------------------------------------------------------
@skip_no_proxy
def test_health():
    r = httpx.get(f"{BASE_URL}/_forge/health", timeout=5.0)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

    status = _get_status()
    assert "tool_selection" in status
    assert "local_models" in status
    assert "remote_models" in status
    assert status["tool_selection"]["max"] > 0


# ------------------------------------------------------------------
# §20.3 count_tokens 熔断
# ------------------------------------------------------------------
@skip_no_proxy
def test_count_tokens_circuit_breaker():
    was_up_before = _is_port_listening(8080)

    payload = {
        "model": LOCAL_MODEL,
        "messages": [{"role": "user", "content": "在吗"}],
        "tools": _make_synthetic_tools(25),
    }
    t0 = time.time()
    r = httpx.post(f"{BASE_URL}/v1/messages/count_tokens?beta=true", json=payload, timeout=5.0)
    elapsed = time.time() - t0

    assert r.status_code == 200
    body = r.json()
    assert isinstance(body.get("input_tokens"), int) and body["input_tokens"] > 0
    assert elapsed < 1.0, f"count_tokens 耗时 {elapsed:.2f}s，应远小于 1s"

    if not was_up_before:
        assert not _is_port_listening(8080), "count_tokens 不应触发 8080 冷启动"


# ------------------------------------------------------------------
# §20.4 本地工具数量限制
# ------------------------------------------------------------------
@skip_no_proxy
def test_local_tool_limit():
    tools = _make_synthetic_tools(25)
    payload = {
        "model": LOCAL_MODEL,
        "max_tokens": 64,
        "messages": [{"role": "user", "content": "在吗"}],
        "tools": tools,
        "stream": False,
    }
    r = httpx.post(f"{BASE_URL}/v1/messages?beta=true", json=payload, timeout=180.0)
    assert r.status_code == 200

    status = _get_status()
    reduction = status["tool_selection"]["last_reduction"]
    assert reduction.get("original") == 25
    assert reduction.get("final") <= status["tool_selection"]["max"]
    assert reduction.get("mode") not in (None, "remote_full", "tool_choice_none")


# ------------------------------------------------------------------
# §20.5 远程全量转发（自包含 mock 后端）
# 依赖本文档给出的 smart_proxy.py 补丁（补充 remote_full 记录）
# ------------------------------------------------------------------
def test_remote_full_forward(monkeypatch):
    import asyncio
    import _infra.smart_proxy as sp
    from httpx import ASGITransport, AsyncClient

    tools = _make_synthetic_tools(25)
    remote_model_name = "test-remote-opus"
    api_key_env = "TEST_REMOTE_API_KEY"

    monkeypatch.setitem(sp.REMOTE_ROUTES, remote_model_name, {
        "api_base": "https://mock-remote.invalid/v1",
        "model": "mock/remote-model",
        "api_key_env": api_key_env,
        "max_tokens": 16384,
    })
    monkeypatch.setenv(api_key_env, "dummy-key")

    def fail_if_selector_called(*a, **kw):
        raise AssertionError("远程请求绝不能调用本地 selector（文档 §10.2）")

    monkeypatch.setattr(sp, "_apply_tool_selection", fail_if_selector_called)

    captured = {}

    async def fake_post(url, json=None, headers=None):
        captured["payload"] = json
        return httpx.Response(
            200,
            json={
                "choices": [{
                    "message": {"role": "assistant", "content": "ok"},
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 42, "completion_tokens": 5},
            },
        )

    monkeypatch.setattr(sp.http_client, "post", fake_post)

    async def _run():
        transport = ASGITransport(app=sp.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "model": remote_model_name,
                "max_tokens": 64,
                "messages": [{"role": "user", "content": "hi"}],
                "tools": tools,
                "stream": False,
            }
            return await client.post("/v1/messages?beta=true", json=payload)

    resp = asyncio.run(_run())
    assert resp.status_code == 200

    forwarded_tools = captured["payload"].get("tools", [])
    assert len(forwarded_tools) == len(tools) == 25
    forwarded_names = {t["function"]["name"] for t in forwarded_tools}
    original_names = {t["name"] for t in tools}
    assert forwarded_names == original_names

    for t in forwarded_tools:
        fname = t["function"]["name"]
        orig = next(x for x in tools if x["name"] == fname)
        assert t["function"]["description"] == orig["description"]
        assert t["function"]["parameters"] == orig["input_schema"]

    with sp._last_reduction_lock:
        info = dict(sp._last_reduction_info)
    assert info.get("mode") == "remote_full"
    assert info.get("original") == 25
    assert info.get("final") == 25


# ------------------------------------------------------------------
# §20.6 强制工具（真实本地模型）
# ------------------------------------------------------------------
@skip_no_proxy
def test_forced_tool_choice():
    tools = _make_synthetic_tools(24) + [_weather_tool()]
    payload = {
        "model": LOCAL_MODEL,
        "max_tokens": 128,
        "messages": [{"role": "user", "content": "What's the weather in Beijing?"}],
        "tools": tools,
        "tool_choice": {"type": "tool", "name": "get_weather"},
        "stream": False,
    }
    r = httpx.post(f"{BASE_URL}/v1/messages?beta=true", json=payload, timeout=180.0)
    assert r.status_code == 200
    body = r.json()

    status = _get_status()
    reduction = status["tool_selection"]["last_reduction"]
    assert reduction["mode"] == "forced_tool_choice"
    assert "get_weather" in reduction["selected"]
    assert reduction["final"] <= status["tool_selection"]["max"]

    tool_use_blocks = [b for b in body.get("content", []) if b.get("type") == "tool_use"]
    assert len(tool_use_blocks) >= 1
    assert tool_use_blocks[0]["name"] == "get_weather"
    assert tool_use_blocks[0]["id"].startswith("toolu_")
    assert not tool_use_blocks[0]["id"].startswith("toolu_toolu_")


# ------------------------------------------------------------------
# §20.7 tool_result 回合
# ------------------------------------------------------------------
@skip_no_proxy
def test_tool_result_turn():
    tools = _make_synthetic_tools(24) + [_weather_tool()]

    turn1 = {
        "model": LOCAL_MODEL,
        "max_tokens": 128,
        "messages": [{"role": "user", "content": "What's the weather in Beijing?"}],
        "tools": tools,
        "tool_choice": {"type": "tool", "name": "get_weather"},
        "stream": False,
    }
    r1 = httpx.post(f"{BASE_URL}/v1/messages?beta=true", json=turn1, timeout=180.0)
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["stop_reason"] == "tool_use"
    tool_use = next(b for b in body1["content"] if b["type"] == "tool_use")
    tool_id = tool_use["id"]

    turn2 = {
        "model": LOCAL_MODEL,
        "max_tokens": 128,
        "messages": [
            {"role": "user", "content": "What's the weather in Beijing?"},
            {"role": "assistant", "content": [tool_use]},
            {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tool_id, "content": "北京当前天气：晴，气温25°C。"}
            ]},
        ],
        "tools": tools,
        "stream": False,
    }
    r2 = httpx.post(f"{BASE_URL}/v1/messages?beta=true", json=turn2, timeout=180.0)
    assert r2.status_code == 200
    body2 = r2.json()

    status = _get_status()
    reduction = status["tool_selection"]["last_reduction"]
    assert reduction["final"] <= status["tool_selection"]["max"]
    assert reduction["final"] < 25, "第二轮不应恢复全量工具"

    assert not tool_id.startswith("toolu_toolu_")
    assert body2["stop_reason"] == "end_turn"


# ------------------------------------------------------------------
# §20.9 SSE 流式文本 + ping
# ------------------------------------------------------------------
@skip_no_proxy
def test_streaming_text_and_ping():
    payload = {
        "model": LOCAL_MODEL,
        "max_tokens": 64,
        "messages": [{"role": "user", "content": "在吗，用一句话回答"}],
        "stream": True,
    }
    events = []
    t0 = time.time()
    with httpx.stream("POST", f"{BASE_URL}/v1/messages?beta=true", json=payload, timeout=180.0) as r:
        assert r.status_code == 200
        current_event = None
        for line in r.iter_lines():
            if not line:
                continue
            if line.startswith("event:"):
                current_event = line.split(":", 1)[1].strip()
                events.append(current_event)
            if current_event == "message_stop":
                break
    elapsed = time.time() - t0

    assert events[0] == "message_start"
    assert events[-1] == "message_stop"
    assert "content_block_start" in events
    assert "content_block_delta" in events
    assert "content_block_stop" in events
    assert events.index("content_block_start") < events.index("content_block_delta")
    assert events.index("content_block_delta") < events.index("content_block_stop")

    if elapsed > PING_INTERVAL * 1.5:
        assert "ping" in events, "长 TTFT 期间应出现心跳 ping（文档 §11.8）"


# ------------------------------------------------------------------
# §20.10 SSE 流式工具调用
# ------------------------------------------------------------------
@skip_no_proxy
def test_streaming_tool_call():
    tools = _make_synthetic_tools(24) + [_weather_tool()]
    payload = {
        "model": LOCAL_MODEL,
        "max_tokens": 128,
        "messages": [{"role": "user", "content": "What's the weather in Shanghai?"}],
        "tools": tools,
        "tool_choice": {"type": "tool", "name": "get_weather"},
        "stream": True,
    }
    events = []
    with httpx.stream("POST", f"{BASE_URL}/v1/messages?beta=true", json=payload, timeout=180.0) as r:
        assert r.status_code == 200
        current_event = None
        for line in r.iter_lines():
            if not line:
                continue
            if line.startswith("event:"):
                current_event = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                try:
                    data = json.loads(line[5:].strip())
                except Exception:
                    data = None
                events.append((current_event, data))
            if current_event == "message_stop":
                break

    tool_start = next(
        (d for (e, d) in events if e == "content_block_start"
         and d.get("content_block", {}).get("type") == "tool_use"), None
    )
    assert tool_start is not None
    assert tool_start["content_block"]["name"] == "get_weather"
    assert tool_start["content_block"]["id"].startswith("toolu_")

    json_fragments = [
        d["delta"]["partial_json"] for (e, d) in events
        if e == "content_block_delta" and d.get("delta", {}).get("type") == "input_json_delta"
    ]
    assert json_fragments, "工具参数首片段不能丢失（文档 §11.5）"
    parsed = json.loads("".join(json_fragments))
    assert "city" in parsed

    message_delta = next((d for (e, d) in events if e == "message_delta"), None)
    assert message_delta is not None
    assert message_delta["delta"]["stop_reason"] == "tool_use"


# ------------------------------------------------------------------
# §20.11 usage
# ------------------------------------------------------------------
@skip_no_proxy
def test_usage_never_zero():
    payload = {
        "model": LOCAL_MODEL,
        "max_tokens": 64,
        "messages": [{"role": "user", "content": "请用一句话介绍你自己"}],
        "stream": False,
    }
    r = httpx.post(f"{BASE_URL}/v1/messages?beta=true", json=payload, timeout=180.0)
    assert r.status_code == 200
    usage = r.json()["usage"]
    assert usage["input_tokens"] > 0
    assert usage["output_tokens"] > 0


# ------------------------------------------------------------------
# §20.12 本地冷暖缓存（默认跳过，涉及分钟级冷 prefill）
# ------------------------------------------------------------------
@skip_no_proxy
@pytest.mark.skipif(not RUN_SLOW, reason="需要 RUN_SLOW=1，涉及冷 prefill 耗时测试")
def test_warm_cold_cache():
    tools = _make_synthetic_tools(9)  # >8 触发 selector，且固定不变以获得稳定前缀
    payload = {
        "model": LOCAL_MODEL,
        "max_tokens": 32,
        "messages": [{"role": "user", "content": "在吗，稳定前缀缓存测试标记 ABC123"}],
        "tools": tools,
        "stream": False,
    }

    t0 = time.time()
    r1 = httpx.post(f"{BASE_URL}/v1/messages?beta=true", json=payload, timeout=300.0)
    cold_elapsed = time.time() - t0
    assert r1.status_code == 200

    t1 = time.time()
    r2 = httpx.post(f"{BASE_URL}/v1/messages?beta=true", json=payload, timeout=300.0)
    warm_elapsed = time.time() - t1
    assert r2.status_code == 200

    assert warm_elapsed < cold_elapsed * 0.25, (
        f"warm={warm_elapsed:.2f}s cold={cold_elapsed:.2f}s，未观察到明显缓存命中（文档 §20.12）"
    )


# ------------------------------------------------------------------
# 新增: 未知模型必须被拒绝，而不是静默回退 8080（§3.3）
# ------------------------------------------------------------------
@skip_no_proxy
def test_unknown_model_rejected():
    payload = {
        "model": UNKNOWN_MODEL,
        "max_tokens": 16,
        "messages": [{"role": "user", "content": "hi"}],
        "stream": False,
    }
    r = httpx.post(f"{BASE_URL}/v1/messages?beta=true", json=payload, timeout=10.0)
    assert r.status_code in (400, 404), (
        f"未知模型应被明确拒绝，实际返回 {r.status_code}（默认 FORGE_ALLOW_UNKNOWN_MODEL_FALLBACK=0）"
    )


# ------------------------------------------------------------------
# 新增: tool_choice=none 不应转发工具 schema（§9.5，依赖 smart_proxy.py 补丁）
# ------------------------------------------------------------------
@skip_no_proxy
def test_tool_choice_none():
    tools = _make_synthetic_tools(25)
    payload = {
        "model": LOCAL_MODEL,
        "max_tokens": 32,
        "messages": [{"role": "user", "content": "在吗"}],
        "tools": tools,
        "tool_choice": {"type": "none"},
        "stream": False,
    }
    t0 = time.time()
    r = httpx.post(f"{BASE_URL}/v1/messages?beta=true", json=payload, timeout=180.0)
    elapsed = time.time() - t0
    assert r.status_code == 200

    status = _get_status()
    reduction = status["tool_selection"]["last_reduction"]
    assert reduction.get("mode") == "tool_choice_none"
    assert reduction.get("original") == 25
    assert reduction.get("final") == 0
    # 间接验证：未转发 25 个大 schema，不应触发分钟级冷 prefill
    assert elapsed < 60.0


# ------------------------------------------------------------------
# 新增: 客户端断开连接应取消后端请求
# ------------------------------------------------------------------
@skip_no_proxy
def test_client_disconnect_cancels_backend():
    status_before = _get_status()
    baseline_active = status_before["active_requests"]

    payload = {
        "model": LOCAL_MODEL,
        "max_tokens": 200,
        "messages": [{"role": "user", "content": "请写一篇 500 字的作文"}],
        "stream": True,
    }
    with httpx.stream("POST", f"{BASE_URL}/v1/messages?beta=true", json=payload, timeout=60.0) as r:
        assert r.status_code == 200
        it = r.iter_lines()
        next(it, None)  # 读一行后立刻断开

    time.sleep(2.0)  # 给 finally 清理逻辑一点时间
    status_after = _get_status()
    assert status_after["active_requests"] <= baseline_active


# ------------------------------------------------------------------
# §20.15 飞书 hook（可选）
# ------------------------------------------------------------------
@pytest.mark.skipif(not RUN_HOOK_TEST, reason="需要 RUN_HOOK_TEST=1")
def test_feishu_hook_timeout():
    hook_path = Path.home() / ".claude" / "hooks" / "feishu-notify.sh"
    if not hook_path.exists():
        pytest.skip("feishu-notify.sh 不存在")
    try:
        subprocess.run(["bash", str(hook_path)], capture_output=True, timeout=10)
    except subprocess.TimeoutExpired:
        pytest.fail("飞书 hook 超过 10 秒未退出，可能导致 Claude Code CLI 卡住（文档 §17.1）")


# ------------------------------------------------------------------
# §20.14 真实 Claude Code：无法完全自动化，人工步骤
# ------------------------------------------------------------------
MANUAL_CHECKLIST_20_14 = """
§20.14 真实 Claude Code 人工验收步骤：

1. 确保 ~/.claude/settings.json 中所有 ANTHROPIC_*_MODEL 指向 claude-haiku-4-5。
2. 运行：claude -p "在吗"
3. 检查 /tmp/forge_smart_proxy.log，应出现类似：
       original_tools=25 forwarded_tools<=8 route=local
4. 记录首字节与总耗时，应明显低于"25 个完整 schema 全量转发"的基线（约 90~260s）。
5. 修改 ~/.claude/settings.json，将所有 ANTHROPIC_*_MODEL 改为 claude-opus-4-8。
6. 重新运行：claude -p "在吗"
7. 检查日志确认：
       original_tools=25 forwarded_tools=25 route=remote
8. 恢复 settings.json 到本地模型配置。
"""

if __name__ == "__main__":
    print(MANUAL_CHECKLIST_20_14)
    raise SystemExit(pytest.main([__file__, "-v"]))
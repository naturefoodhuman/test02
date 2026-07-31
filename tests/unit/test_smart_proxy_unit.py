"""
tests/unit/test_smart_proxy_unit.py

对应交接文档 §21 "unit（单元测试）" 一栏。
直接 import _infra.smart_proxy，不启动任何网络服务，通过 monkeypatch
掉所有网络调用（_select_tools_stage1 / http_client.post）来精确验证
内部决策逻辑。不需要 8080 / 4000 实际跑起来。

运行方式：
    pytest tests/unit/test_smart_proxy_unit.py -v

覆盖关系：
    test_no_schema_truncation              -> §20.4（深度相等/不截断精确化）
    test_forced_tool_choice_not_found      -> §20.6
    test_used_tools_survive_tool_result    -> §20.7
    test_selector_failure_heuristic_fallback -> §20.8
    test_retry_policy                      -> §12（重试策略，新增）
    test_cache_key_includes_schema_hash    -> §9.10（新增）
    test_selection_order_stable            -> §9.7（新增）
    test_model_runtime_expand_recursive    -> §14.4（新增）
"""

import asyncio
import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import _infra.smart_proxy as sp  # noqa: E402
import _infra.model_runtime as mr  # noqa: E402


# ------------------------------------------------------------------
# 测试数据构造
# ------------------------------------------------------------------
def _make_tool(name, desc_len=50, extra_props=3):
    return {
        "name": name,
        "description": ("D" * desc_len) + f"_{name}",
        "input_schema": {
            "type": "object",
            "properties": {
                f"p{i}": {"type": "string", "description": f"prop {i} of {name}"}
                for i in range(extra_props)
            },
            "required": ["p0"],
        },
    }


def _make_synthetic_tools(n=25):
    return [_make_tool(f"Tool{i:02d}") for i in range(n)]


def _run(coro):
    return asyncio.run(coro)


# ------------------------------------------------------------------
# §20.4 精确化：已选工具 schema 深度相等，不被截断
# ------------------------------------------------------------------
def test_no_schema_truncation(monkeypatch):
    tools = _make_synthetic_tools(25)
    tools_by_name = {t["name"]: copy.deepcopy(t) for t in tools}

    async def fake_stage1(user_text, tools_in, target_port, real_model_id):
        return ["Tool00", "Tool01", "Tool02"]

    monkeypatch.setattr(sp, "_select_tools_stage1", fake_stage1)

    data = {
        "messages": [{"role": "user", "content": "please use Tool00 and Tool01"}],
        "tools": tools,
    }
    result = _run(sp._apply_tool_selection(data, target_port=8080, real_model_id="test-model"))

    assert len(result["tools"]) <= sp.FORGE_TOOL_SELECTION_MAX
    assert len(result["tools"]) > 0
    for t in result["tools"]:
        original = tools_by_name[t["name"]]
        # 只允许"数量减少"，绝不允许对已选中工具的 description / input_schema 做任何裁剪
        assert t["description"] == original["description"], "description 被截断"
        assert t["input_schema"] == original["input_schema"], "input_schema 被截断"


# ------------------------------------------------------------------
# §20.6: 强制工具但工具名不存在时，不应触发 selector，且回退到 Core Tools
# ------------------------------------------------------------------
def test_forced_tool_choice_not_found(monkeypatch):
    tools = _make_synthetic_tools(25)

    def fail_if_called(*a, **kw):
        raise AssertionError("tool_choice=forced 时绝不应调用 stage1 selector（文档 §9.5）")

    monkeypatch.setattr(sp, "_select_tools_stage1", fail_if_called)

    data = {
        "messages": [{"role": "user", "content": "hello"}],
        "tools": tools,
        "tool_choice": {"type": "tool", "name": "NonExistentTool"},
    }
    result = _run(sp._apply_tool_selection(data, target_port=8080, real_model_id="test-model"))

    assert 0 < len(result["tools"]) <= sp.FORGE_TOOL_SELECTION_MAX
    with sp._last_reduction_lock:
        mode = sp._last_reduction_info.get("mode")
    assert mode == "forced_tool_choice_not_found_fallback_core"


# ------------------------------------------------------------------
# §20.7: tool_result 回合不能丢失已使用工具，也不能因此恢复全量工具
# ------------------------------------------------------------------
def test_used_tools_survive_tool_result(monkeypatch):
    tools = _make_synthetic_tools(25)
    used_name = "Tool05"

    async def fake_stage1(user_text, tools_in, target_port, real_model_id):
        # 模拟 selector 因为看不到早期 user 意图，认为不需要任何工具
        return []

    monkeypatch.setattr(sp, "_select_tools_stage1", fake_stage1)

    messages = [
        {"role": "user", "content": "please run Tool05 to check status"},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "toolu_abc123", "name": used_name, "input": {}}
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "toolu_abc123", "content": "ok"}
        ]},
    ]
    data = {"messages": messages, "tools": tools}
    result = _run(sp._apply_tool_selection(data, target_port=8080, real_model_id="test-model"))

    names = {t["name"] for t in result["tools"]}
    assert used_name in names, "已使用工具必须在 tool_result 回合后继续存在"
    assert len(result["tools"]) <= sp.FORGE_TOOL_SELECTION_MAX
    assert len(result["tools"]) < len(tools), "不能因为纯 tool_result 回合而恢复全量工具"


# ------------------------------------------------------------------
# §20.8: selector 失败时的确定性启发式兜底
# ------------------------------------------------------------------
def test_selector_failure_heuristic_fallback(monkeypatch):
    tools = _make_synthetic_tools(25)
    tools_by_name = {t["name"]: t for t in tools}
    tools_by_name["Tool03"]["description"] = "reads a configuration file from disk"

    async def fake_stage1(user_text, tools_in, target_port, real_model_id):
        return None  # 模拟非法 JSON / 超时

    monkeypatch.setattr(sp, "_select_tools_stage1", fake_stage1)

    data = {
        "messages": [{"role": "user", "content": "please read the configuration file"}],
        "tools": tools,
    }

    result1 = _run(sp._apply_tool_selection(copy.deepcopy(data), 8080, "test-model"))
    with sp._last_reduction_lock:
        mode1 = sp._last_reduction_info.get("mode")
    assert mode1 == "heuristic_fallback"
    assert 0 < len(result1["tools"]) <= sp.FORGE_TOOL_SELECTION_MAX
    names1 = [t["name"] for t in result1["tools"]]
    assert "Tool03" in names1, "启发式打分应命中描述中的关键词"

    # 代理不能因为 selector 失败而 500，也不能全量转发（已在上面 assert 覆盖数量）
    # 确定性：相同输入两次调用应得到相同顺序
    result2 = _run(sp._apply_tool_selection(copy.deepcopy(data), 8080, "test-model"))
    names2 = [t["name"] for t in result2["tools"]]
    assert names1 == names2, "heuristic_fallback 必须是确定性的，两次结果应完全一致"


# ------------------------------------------------------------------
# 新增: 重试策略（§12）
# ------------------------------------------------------------------
def test_retry_policy(monkeypatch):
    import httpx

    monkeypatch.setattr(sp.asyncio, "sleep", _fast_sleep)

    # Case 1: 可重试状态码 502，远程 retry_count=2 -> 最多尝试 3 次
    monkeypatch.setattr(sp, "FORGE_REMOTE_RETRY_COUNT", 2)
    calls = []

    async def post_502(url, json=None, headers=None):
        calls.append(502)
        return httpx.Response(502, text="bad gateway")

    monkeypatch.setattr(sp.http_client, "post", post_502)
    resp, err = _run(sp._forward_with_retries("http://x", {}, {}, is_remote=True, target_port=None))
    assert len(calls) == 3, "502 属于可重试状态码，应重试到 max_attempts"
    assert resp.status_code == 502

    # Case 2: 不可重试状态码 400 -> 只应尝试 1 次
    calls.clear()

    async def post_400(url, json=None, headers=None):
        calls.append(400)
        return httpx.Response(400, text="bad request")

    monkeypatch.setattr(sp.http_client, "post", post_400)
    resp2, err2 = _run(sp._forward_with_retries("http://x", {}, {}, is_remote=True, target_port=None))
    assert len(calls) == 1, "400/401/403/404/422 不应重试（文档 §12）"
    assert resp2.status_code == 400

    # Case 3: 本地默认 retry_count=0，502 也只应尝试 1 次
    monkeypatch.setattr(sp, "FORGE_LOCAL_RETRY_COUNT", 0)
    calls.clear()

    async def post_502_local(url, json=None, headers=None):
        calls.append(502)
        return httpx.Response(502, text="bad gateway")

    monkeypatch.setattr(sp.http_client, "post", post_502_local)
    resp3, err3 = _run(sp._forward_with_retries("http://x", {}, {}, is_remote=False, target_port=8080))
    assert len(calls) == 1, "本地长生成默认不应重试（文档 §12 / §19 FORGE_LOCAL_RETRY_COUNT=0）"


async def _fast_sleep(_):
    return None


# ------------------------------------------------------------------
# 新增: 缓存 key 必须包含 schema 指纹，而不仅是工具名集合（§9.10）
# ------------------------------------------------------------------
def test_cache_key_includes_schema_hash(monkeypatch):
    calls = []

    async def counting_stage1(user_text, tools_in, target_port, real_model_id):
        calls.append(1)
        return ["Tool00"]

    monkeypatch.setattr(sp, "_select_tools_stage1", counting_stage1)
    sp.tool_selection_cache.cache.clear()
    sp.tool_selection_cache.order.clear()

    tools_v1 = _make_synthetic_tools(25)
    data1 = {"messages": [{"role": "user", "content": "do something with Tool00"}], "tools": tools_v1}

    _run(sp._apply_tool_selection(copy.deepcopy(data1), 8080, "test-model"))
    assert len(calls) == 1, "首次调用必须触发 selector（未命中缓存）"

    _run(sp._apply_tool_selection(copy.deepcopy(data1), 8080, "test-model"))
    assert len(calls) == 1, "完全相同输入应命中缓存，selector 不应被再次调用"

    tools_v2 = copy.deepcopy(tools_v1)
    tools_v2[0]["description"] += " (schema updated)"
    data2 = {"messages": [{"role": "user", "content": "do something with Tool00"}], "tools": tools_v2}

    _run(sp._apply_tool_selection(copy.deepcopy(data2), 8080, "test-model"))
    assert len(calls) == 2, (
        "仅工具名集合不变但 schema/description 变化，必须视为缓存未命中，"
        "否则说明缓存 key 只依赖工具名而非 schema 指纹（违反 §9.10）"
    )


# ------------------------------------------------------------------
# 新增: 最终工具集合顺序必须稳定（不能来自 set()）（§9.7）
# ------------------------------------------------------------------
def test_selection_order_stable(monkeypatch):
    tools = _make_synthetic_tools(25)

    async def fake_stage1(user_text, tools_in, target_port, real_model_id):
        return ["Tool09", "Tool01", "Tool05"]  # 故意乱序返回

    monkeypatch.setattr(sp, "_select_tools_stage1", fake_stage1)
    sp.tool_selection_cache.cache.clear()
    sp.tool_selection_cache.order.clear()

    data = {"messages": [{"role": "user", "content": "use Tool09 Tool01 Tool05"}], "tools": tools}
    result1 = _run(sp._apply_tool_selection(copy.deepcopy(data), 8080, "test-model"))
    names1 = [t["name"] for t in result1["tools"]]
    assert names1 == sorted(names1), "最终工具必须按名称稳定排序"

    result2 = _run(sp._apply_tool_selection(copy.deepcopy(data), 8080, "test-model"))
    names2 = [t["name"] for t in result2["tools"]]
    assert names1 == names2, "重复调用（含缓存命中）结果顺序必须完全一致"


# ------------------------------------------------------------------
# §14.4: model_runtime._expand 必须递归处理 list/dict
# ------------------------------------------------------------------
def test_model_runtime_expand_recursive():
    home = str(Path.home())
    value = {
        "extra_args": [
            "--ssd-session-cache-dir",
            "${HOME}/.mtplx/session_cache/8080",
            {"nested": ["${HOME}/x", 123, None]},
        ],
        "plain": "${HOME}/plain",
        "untouched": 42,
    }
    out = mr._expand(value)

    assert out["extra_args"][1] == f"{home}/.mtplx/session_cache/8080"
    assert out["extra_args"][2]["nested"][0] == f"{home}/x"
    assert out["extra_args"][2]["nested"][1] == 123
    assert out["extra_args"][2]["nested"][2] is None
    assert out["plain"] == f"{home}/plain"
    assert out["untouched"] == 42
    assert "${HOME}" not in out["extra_args"][1]

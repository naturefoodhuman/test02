# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-03 05:59:05
#
# 单测：smart_proxy 上下文预算 guard（防上游 GLM 5.2 超长 400）。
# 覆盖：
#   1. _estimate_messages_tokens 口径与 count_tokens 端点一致
#   2. _compact_messages：system/最近N轮/tool 配对不被裁剪；长 tool_result/assistant 被截断
#   3. _apply_context_budget：低于 SOFT 放行；达 SOFT 触发裁剪且 token 数下降；
#      达 HARD 且裁剪后仍超 HARD → rejected；达 HARD 但裁剪后降到 HARD 以下 → compacted
#   4. guard 触发后 forward_payload["messages"] 被原地修改（compacted）或不变（rejected）

import sys
import os

_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import _infra.smart_proxy as sp  # noqa: E402

import json as _json


def json_dumps(m):
    return _json.dumps(m, ensure_ascii=False)


# ============================================================
# 1. 估算口径
# ============================================================
class TestEstimateTokens:
    def test_empty_messages(self):
        assert sp._estimate_messages_tokens([]) == 0
        assert sp._estimate_messages_tokens(None) == 0

    def test_matches_count_tokens_endpoint(self):
        """估算口径必须与 /messages/count_tokens 端点一致：_json_bytes // DIVISOR。"""
        msgs = [
            {"role": "system", "content": "you are helpful"},
            {"role": "user", "content": "hello world"},
        ]
        expected = max(1, sp._json_bytes(msgs) // sp.FORGE_COUNT_TOKENS_DIVISOR)
        assert sp._estimate_messages_tokens(msgs) == expected

    def test_grows_with_size(self):
        small = [{"role": "user", "content": "x" * 100}]
        big = [{"role": "user", "content": "x" * 10000}]
        assert sp._estimate_messages_tokens(big) > sp._estimate_messages_tokens(small)


# ============================================================
# 2. _compact_messages 裁剪策略
# ============================================================
class TestCompactMessages:
    def test_short_messages_unchanged(self):
        msgs = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
        out = sp._compact_messages(msgs, keep_recent_turns=2, trunc_tool_result_chars=2000)
        assert out == msgs

    def test_system_always_kept(self):
        """system 消息即使在中间历史区也必须完整保留。"""
        sys_msg = {"role": "system", "content": "X" * 5000}
        msgs = [
            sys_msg,
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
        ]
        out = sp._compact_messages(msgs, keep_recent_turns=1, trunc_tool_result_chars=100)
        assert out[0] == sys_msg  # system 完整保留

    def test_recent_turns_kept(self):
        """最近 keep_recent_turns*2 条 user/assistant 完整保留。"""
        msgs = [
            {"role": "user", "content": "old1"},
            {"role": "assistant", "content": "old2"},
            {"role": "user", "content": "recent_u"},
            {"role": "assistant", "content": "recent_a"},
        ]
        out = sp._compact_messages(msgs, keep_recent_turns=1, trunc_tool_result_chars=100)
        # 最近 1 轮 = 最后 2 条，必须完整
        assert out[-1] == msgs[-1]
        assert out[-2] == msgs[-2]

    def test_tool_calls_pair_kept(self):
        """含 tool_calls / tool_call_id 的消息必须保留（保证工具调用配对完整）。"""
        msgs = [
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "thinking", "tool_calls": [
                {"id": "c1", "type": "function", "function": {"name": "f", "arguments": "{}"}}
            ]},
            {"role": "tool", "tool_call_id": "c1", "content": "result"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
        ]
        out = sp._compact_messages(msgs, keep_recent_turns=1, trunc_tool_result_chars=100)
        # tool_calls 和 tool_call_id 配对都应在输出中
        contents = [json_dumps(m) for m in out]
        assert any("tool_calls" in c for c in contents)
        assert any("tool_call_id" in c for c in contents)

    def test_long_tool_result_truncated(self):
        """超长 tool_result content 被截断到 trunc_tool_result_chars，并加截断标记。"""
        long_result = "R" * 5000
        msgs = [
            {"role": "user", "content": "u1"},
            {"role": "tool", "tool_call_id": "c1", "content": long_result},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
        ]
        out = sp._compact_messages(msgs, keep_recent_turns=1, trunc_tool_result_chars=200)
        # 找到 tool 消息
        tool_msgs = [m for m in out if m.get("role") == "tool"]
        assert tool_msgs, "tool 消息不应被整条删除（含 tool_call_id 必须保留）"
        # 但其 content 应被截断
        assert len(tool_msgs[0]["content"]) < len(long_result)
        assert "truncated" in tool_msgs[0]["content"]

    def test_long_assistant_text_truncated(self):
        """超长 assistant 文本输出被裁成首尾骨架。"""
        long_text = "A" * 5000
        msgs = [
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": long_text},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
        ]
        out = sp._compact_messages(msgs, keep_recent_turns=1, trunc_tool_result_chars=100)
        asst_msgs = [m for m in out if m.get("role") == "assistant" and isinstance(m.get("content"), str)]
        # 中间那条长 assistant 应被截断
        truncated = [m for m in asst_msgs if "truncated" in m["content"]]
        assert truncated, "长 assistant 输出应被截断"
        assert all(len(m["content"]) < len(long_text) for m in truncated)

    def test_compact_reduces_token_count(self):
        """裁剪后 token 估算数必须下降。"""
        msgs = [
            {"role": "system", "content": "S" * 200},
            {"role": "user", "content": "U" * 200},
            {"role": "assistant", "content": "A" * 4000},
            {"role": "user", "content": "U" * 200},
            {"role": "assistant", "content": "A" * 4000},
            {"role": "user", "content": "recent"},
            {"role": "assistant", "content": "recent_a"},
        ]
        before = sp._estimate_messages_tokens(msgs)
        out = sp._compact_messages(msgs, keep_recent_turns=1, trunc_tool_result_chars=500)
        after = sp._estimate_messages_tokens(out)
        assert after < before


# ============================================================
# 3. _apply_context_budget 决策
# ============================================================
class TestApplyContextBudget:
    def test_below_soft_passes(self):
        """低于 SOFT 阈值：放行，messages 不变。"""
        msgs = [{"role": "user", "content": "small"}]
        payload = {"messages": msgs}
        action, eb, ea, hint = sp._apply_context_budget(payload)
        assert action == "pass"
        assert hint == ""
        assert payload["messages"] is msgs  # 未修改

    def test_soft_triggers_compaction(self, monkeypatch):
        """达 SOFT 但未达 HARD：触发裁剪，token 数下降，messages 被替换。"""
        monkeypatch.setattr(sp, "FORGE_CTX_MAX_TOKENS", 10000)
        monkeypatch.setattr(sp, "FORGE_CTX_SOFT_RATIO", 0.80)
        monkeypatch.setattr(sp, "FORGE_CTX_HARD_RATIO", 0.95)
        monkeypatch.setattr(sp, "FORGE_CTX_KEEP_RECENT_TURNS", 1)
        monkeypatch.setattr(sp, "FORGE_CTX_TRUNC_TOOL_RESULT_CHARS", 200)
        # 构造 ~8500 tokens（>8000 SOFT，<9500 HARD）
        msgs = [
            {"role": "system", "content": "S" * 200},
            {"role": "user", "content": "U" * 5000},
            {"role": "assistant", "content": "A" * 30000},  # 大段可裁
            {"role": "user", "content": "recent"},
            {"role": "assistant", "content": "recent_a"},
        ]
        payload = {"messages": msgs}
        action, eb, ea, hint = sp._apply_context_budget(payload)
        assert action == "compacted"
        assert ea < eb
        assert "80%" in hint
        assert "/compact" in hint
        assert payload["messages"] is not msgs  # 已被替换

    def test_hard_rejects_when_compaction_insufficient(self, monkeypatch):
        """达 HARD 且裁剪后仍超 HARD：rejected，messages 不被采用。"""
        monkeypatch.setattr(sp, "FORGE_CTX_MAX_TOKENS", 1000)
        monkeypatch.setattr(sp, "FORGE_CTX_SOFT_RATIO", 0.80)
        monkeypatch.setattr(sp, "FORGE_CTX_HARD_RATIO", 0.95)
        monkeypatch.setattr(sp, "FORGE_CTX_KEEP_RECENT_TURNS", 1)
        monkeypatch.setattr(sp, "FORGE_CTX_TRUNC_TOOL_RESULT_CHARS", 100)
        # 构造远超上限的 messages：即使裁剪也降不到 950 以下
        msgs = [
            {"role": "system", "content": "S" * 50000},
            {"role": "user", "content": "U" * 50000},
            {"role": "assistant", "content": "A" * 50000},
            {"role": "user", "content": "recent"},
            {"role": "assistant", "content": "recent_a"},
        ]
        payload = {"messages": msgs}
        action, eb, ea, hint = sp._apply_context_budget(payload)
        assert action == "rejected"
        assert "95%" in hint
        assert "/compact" in hint

    def test_hard_compacted_when_compaction_sufficient(self, monkeypatch):
        """达 HARD 但裁剪后降到 HARD 以下：compacted（给一次自愈机会）。"""
        monkeypatch.setattr(sp, "FORGE_CTX_MAX_TOKENS", 1000)
        monkeypatch.setattr(sp, "FORGE_CTX_SOFT_RATIO", 0.80)
        monkeypatch.setattr(sp, "FORGE_CTX_HARD_RATIO", 0.95)
        monkeypatch.setattr(sp, "FORGE_CTX_KEEP_RECENT_TURNS", 1)
        monkeypatch.setattr(sp, "FORGE_CTX_TRUNC_TOOL_RESULT_CHARS", 100)
        # 超过 SOFT(800) 和 HARD(950)，但裁剪掉大段 assistant 后能降到 HARD 以下
        msgs = [
            {"role": "system", "content": "S" * 200},
            {"role": "user", "content": "U" * 200},
            {"role": "assistant", "content": "A" * 8000},  # 大段可裁
            {"role": "user", "content": "recent"},
            {"role": "assistant", "content": "recent_a"},
        ]
        payload = {"messages": msgs}
        action, eb, ea, hint = sp._apply_context_budget(payload)
        assert action == "compacted"
        assert ea < eb
        assert ea < 950  # 裁剪后降到 HARD 以下

    def test_empty_messages_passes(self):
        payload = {"messages": []}
        action, eb, ea, hint = sp._apply_context_budget(payload)
        assert action == "pass"
        assert eb == 0


# ============================================================
# 4. 配置常量存在且合理
# ============================================================
class TestConfigConstants:
    def test_defaults_present(self):
        assert sp.FORGE_CTX_MAX_TOKENS > 0
        assert 0 < sp.FORGE_CTX_SOFT_RATIO < sp.FORGE_CTX_HARD_RATIO < 1
        assert sp.FORGE_CTX_KEEP_RECENT_TURNS >= 1
        assert sp.FORGE_CTX_TRUNC_TOOL_RESULT_CHARS > 0

    def test_soft_below_hard(self):
        assert sp.FORGE_CTX_SOFT_RATIO < sp.FORGE_CTX_HARD_RATIO

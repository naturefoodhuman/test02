# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 16:35:00 CST

"""单元测试：ModeManager"""

from _infra.network.mode_manager.manager import ModeManager, get_mode_manager


def test_default_mode():
    mm = ModeManager()
    assert mm.current_mode == "research"


def test_mode_switch():
    mm = ModeManager()
    mm.set_mode("coding")
    assert mm.current_mode == "coding"


def test_research_allows_searxng():
    mm = ModeManager()
    assert mm.is_server_allowed("searxng") is True
    assert mm.is_server_allowed("filesystem") is False


def test_coding_denies_searxng():
    mm = ModeManager()
    mm.set_mode("coding")
    assert mm.is_server_allowed("searxng") is False
    assert mm.is_server_allowed("git") is True


def test_get_profile():
    mm = get_mode_manager()
    profile = mm.get_mode_profile("private")
    assert "allowed_servers" in profile
    assert "chrome-devtools-private" in profile.get("allowed_servers", [])

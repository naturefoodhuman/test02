# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 22:03:00

"""PowerSync probe unit tests."""

from __future__ import annotations

from server.app.sync.service.powersync_probe import normalize_powersync_url


def test_normalize_powersync_url_defaults_to_compose_port() -> None:
    assert normalize_powersync_url(None) == "http://127.0.0.1:9081"


def test_normalize_powersync_url_adds_scheme_and_strips_trailing_slash() -> None:
    assert normalize_powersync_url("127.0.0.1:9081/") == "http://127.0.0.1:9081"
    assert normalize_powersync_url("https://powersync.local/") == "https://powersync.local"

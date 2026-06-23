# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 15:16:58

"""Unit tests for ProfileManager (E7-C3-S1-T1/T2)."""

from pathlib import Path

import pytest

from _infra.network.browser.profile_manager import ProfileManager
from _infra.network.config_loader.schemas import NetworkConfig


def test_profile_manager_loads_config_profiles():
    manager = ProfileManager()
    profiles = manager.list_profiles()

    assert "ai_public" in profiles
    assert "ai_private_github" in profiles


def test_get_ai_public_profile_from_config():
    manager = ProfileManager()
    profile = manager.get_profile("ai_public")

    assert profile.name == "ai_public"
    assert str(profile.user_data_dir).endswith("ai-public")
    assert "https://accounts.google.com" in profile.blocked_origins


def test_get_private_profile_from_config():
    manager = ProfileManager()
    profile = manager.get_profile("ai_private_github")

    assert profile.remote_debugging_port == 9222
    assert "github.com" in profile.allowed_domains


def test_unknown_profile_raises():
    manager = ProfileManager()
    with pytest.raises(KeyError):
        manager.get_profile("missing")


def test_ensure_profile_dir_with_test_root(tmp_path):
    cfg = NetworkConfig(
        browser={
            "profiles": {
                "ai_public": {
                    "user_data_dir": "${HOME}/ai-agent/profiles/ai-public",
                    "blocked_origins": ["https://accounts.google.com"],
                }
            }
        }
    )
    manager = ProfileManager(config=cfg, profile_root=tmp_path)

    created = manager.ensure_profile_dir("ai_public")

    assert created == tmp_path / "ai-public"
    assert created.exists()
    assert created.is_dir()


def test_ai_public_profile_documentation_exists():
    doc = Path("profiles/ai-public/README.md")
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    assert "No private account login" in text
    assert "PrivacyGateway light mode" in text

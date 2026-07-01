# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""FEOS-001 skeleton and default configuration tests."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
DEFAULTS = ROOT / "_infra" / "feos" / "defaults"
CONFIG = ROOT / "config" / "feos.yaml"


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), f"{path} must parse to mapping"
    return data


def test_feos_package_importable():
    import _infra.feos as feos

    assert feos.__version__ == "0.1.0-feos-foundation"


def test_default_and_project_config_parse():
    default_cfg = load_yaml(DEFAULTS / "feos.yaml")
    project_cfg = load_yaml(CONFIG)

    assert default_cfg["feos"]["enabled"] is True
    assert project_cfg["feos"]["enabled"] is True


def test_clipboard_gateway_enabled_and_future_gateways_disabled():
    cfg = load_yaml(CONFIG)["feos"]
    gateways = cfg["gateways"]

    assert gateways["clipboard"]["enabled"] is True
    for name in ["api", "mcp", "browser", "cloud_agent"]:
        assert gateways[name]["enabled"] is False


def test_default_policy_and_renderer_profiles_parse():
    for path in (DEFAULTS / "policies").glob("*.yaml"):
        assert load_yaml(path)

    profile_dir = DEFAULTS / "renderer_profiles"
    profiles = {path.name: load_yaml(path) for path in profile_dir.glob("*.yaml")}
    assert "gpt_markdown_debug.yaml" in profiles
    assert "claude_markdown_architecture.yaml" in profiles
    assert "generic_markdown.yaml" in profiles
    assert "api_json.yaml" in profiles
    assert "mcp_message.yaml" in profiles
    assert profiles["generic_markdown.yaml"]["gateway"] == "clipboard"
    assert profiles["api_json.yaml"]["enabled"] is False
    assert profiles["mcp_message.yaml"]["enabled"] is False


def test_gitignore_contains_feos_runtime_paths():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for item in [
        ".forge/feos/cases/",
        ".forge/feos/metrics/",
        ".forge/feos/cache/",
        ".forge/feos/knowledge_index/",
    ]:
        assert item in gitignore

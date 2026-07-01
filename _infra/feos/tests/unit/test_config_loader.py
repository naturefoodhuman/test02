# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""FEOS-002 config loader and bootstrap tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from _infra.feos.config_loader import FEOSConfigError, bootstrap_feos, load_config, load_yaml_file


def test_load_config_defaults_and_project_overlay():
    cfg = load_config()
    assert cfg.feos.enabled is True
    assert cfg.feos.home == ".forge/feos"
    assert cfg.feos.defaults.gateway == "clipboard"
    assert cfg.feos.gateways.clipboard.enabled is True
    assert cfg.feos.gateways.api.enabled is False
    assert cfg.feos.gateways.mcp.enabled is False
    assert cfg.feos.gateways.browser.enabled is False
    assert cfg.feos.gateways.cloud_agent.enabled is False


def test_env_home_override(monkeypatch, tmp_path):
    monkeypatch.setenv("FEOS_HOME", str(tmp_path / "custom_feos"))
    cfg = load_config()
    assert cfg.feos.home == str(tmp_path / "custom_feos")


def test_env_provider_gateway_and_log_level_override(monkeypatch):
    monkeypatch.setenv("FEOS_DEFAULT_PROVIDER", "claude_web")
    monkeypatch.setenv("FEOS_DEFAULT_GATEWAY", "clipboard")
    monkeypatch.setenv("FEOS_LOG_LEVEL", "debug")
    cfg = load_config()
    assert cfg.feos.defaults.provider == "claude_web"
    assert cfg.feos.defaults.gateway == "clipboard"
    assert cfg.feos.observability.log_level == "DEBUG"


def test_future_gateway_env_defaults_false_and_can_be_enabled(monkeypatch):
    cfg = load_config()
    assert cfg.feos.gateways.api.enabled is False
    assert cfg.feos.gateways.browser.enabled is False

    monkeypatch.setenv("FEOS_ENABLE_API_GATEWAY", "true")
    monkeypatch.setenv("FEOS_ENABLE_BROWSER_GATEWAY", "1")
    cfg2 = load_config()
    assert cfg2.feos.gateways.api.enabled is True
    assert cfg2.feos.gateways.browser.enabled is True
    assert cfg2.feos.gateways.mcp.enabled is False
    assert cfg2.feos.gateways.cloud_agent.enabled is False


def test_cli_overrides_win_over_env(monkeypatch):
    monkeypatch.setenv("FEOS_HOME", ".forge/from_env")
    cfg = load_config(cli_overrides={"home": ".forge/from_cli", "defaults": {"provider": "generic_external_ai"}})
    assert cfg.feos.home == ".forge/from_cli"
    assert cfg.feos.defaults.provider == "generic_external_ai"


def test_bootstrap_context_and_optional_home_creation(tmp_path):
    context = bootstrap_feos(cli_overrides={"home": str(tmp_path / "feos_home")}, create_home=True)
    assert context.feos_home.exists()
    assert context.config.feos.defaults.gateway == "clipboard"


def test_invalid_yaml_reports_clear_error(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("feos: [unterminated", encoding="utf-8")
    with pytest.raises(FEOSConfigError, match="Failed to parse YAML"):
        load_yaml_file(bad)

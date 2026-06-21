# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 15:18:00 CST

"""单元测试：network config_loader（复用现有 FORGE 测试风格）"""

import pytest
from pathlib import Path

from _infra.network.config_loader import load_network_config, NetworkConfig, NetworkConfigError


def test_load_network_config_success(tmp_path):
    """正常加载"""
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "network.yaml"
    cfg_file.write_text("""
version: "1.0"
search:
  searxng:
    base_url: "http://127.0.0.1:8080"
""", encoding="utf-8")

    cfg = load_network_config(project_root=tmp_path)
    assert isinstance(cfg, NetworkConfig)
    assert cfg.search.searxng.base_url == "http://127.0.0.1:8080"
    assert cfg.version == "1.0"


def test_load_network_config_missing_file(tmp_path):
    """缺少文件应报错"""
    with pytest.raises(NetworkConfigError, match="不存在"):
        load_network_config(project_root=tmp_path)


def test_load_network_config_invalid_version(tmp_path):
    """非法版本应报错"""
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    (cfg_dir / "network.yaml").write_text("version: \"2.0\"", encoding="utf-8")

    with pytest.raises(NetworkConfigError):
        load_network_config(project_root=tmp_path)

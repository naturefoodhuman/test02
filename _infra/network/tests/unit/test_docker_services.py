# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-25 00:00:00

"""Static tests for Docker deployment configs (E3-C1 / E4-C1)."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
COMPOSE = ROOT / "docker" / "docker-compose.yml"
SEARXNG_SETTINGS = ROOT / "docker" / "searxng" / "settings.yml"


def load_compose():
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))


def load_settings():
    return yaml.safe_load(SEARXNG_SETTINGS.read_text(encoding="utf-8"))


def test_docker_compose_has_local_only_searxng():
    data = load_compose()
    searxng = data["services"]["searxng"]

    assert searxng["ports"] in (["127.0.0.1:8080:8080"], ["127.0.0.1:8090:8080"])
    assert searxng["restart"] == "unless-stopped"
    assert "searxng/searxng" in searxng["image"]
    assert any("./searxng/settings.yml:/etc/searxng/settings.yml:ro" == volume for volume in searxng["volumes"])


def test_searxng_settings_enable_json_and_disable_google():
    settings = load_settings()

    assert "json" in settings["search"]["formats"]
    assert settings["server"]["bind_address"] == "0.0.0.0"
    assert settings["server"]["port"] == 8080
    assert settings["server"]["secret_key"] == "${SEARXNG_SECRET_KEY}"
    assert settings["outgoing"]["request_timeout"] == 10.0
    assert settings["outgoing"]["max_request_timeout"] == 20.0
    assert settings["outgoing"]["enable_http2"] is False
    keep_only = settings["use_default_settings"]["engines"]["keep_only"]
    assert "wikipedia" in keep_only
    assert "mojeek" in keep_only
    google = [engine for engine in settings["engines"] if engine["name"] == "google"]
    startpage = [engine for engine in settings["engines"] if engine["name"] == "startpage"]
    duckduckgo = [engine for engine in settings["engines"] if engine["name"] == "duckduckgo"]
    assert google and google[0]["disabled"] is True
    assert startpage and startpage[0]["disabled"] is True
    assert duckduckgo and duckduckgo[0]["disabled"] is True


def test_docker_compose_has_local_only_crawl4ai():
    data = load_compose()
    crawl4ai = data["services"]["crawl4ai"]

    assert crawl4ai["ports"] == ["127.0.0.1:11235:11235"]
    assert crawl4ai["restart"] == "unless-stopped"
    assert crawl4ai["shm_size"] == "1g"
    assert "crawl4ai" in crawl4ai["image"]
    assert crawl4ai["environment"]["CRAWL4AI_DISABLE_JS"] == "${CRAWL4AI_DISABLE_JS:-true}"


def test_compose_services_have_healthchecks_and_shared_network():
    data = load_compose()
    assert set(data["services"]) == {"searxng", "crawl4ai"}
    for service in data["services"].values():
        assert "healthcheck" in service
        assert service["networks"] == ["forge-network"]

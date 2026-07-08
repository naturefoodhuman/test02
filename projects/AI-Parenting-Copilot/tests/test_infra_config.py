# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 23:35:00


"""APC-T003 tests for local infrastructure configuration."""

from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_docker_compose_declares_required_services_without_extra_datastore() -> None:
    compose = yaml.safe_load((PROJECT_ROOT / "deploy/docker-compose.yml").read_text())
    services = compose["services"]

    assert {"postgres", "mosquitto", "powersync"}.issubset(services)
    assert services["postgres"]["image"].startswith("postgres:15")
    assert services["mosquitto"]["image"] == "eclipse-mosquitto:2"
    assert services["powersync"]["image"] == "journeyapps/powersync-service:latest"
    assert "mongo" not in services
    assert "wal_level=logical" in services["postgres"]["command"]


def test_powersync_uses_postgres_bucket_storage_to_preserve_architecture_boundary() -> None:
    config = yaml.safe_load((PROJECT_ROOT / "deploy/powersync/service.yaml").read_text())

    assert config["replication"]["connections"][0]["type"] == "postgresql"
    assert config["storage"]["type"] == "postgresql"
    assert config["sync_config"]["path"] == "/config/sync-config.yaml"


def test_alembic_offline_sql_generation_smoke() -> None:
    # No database connection is required while no revisions exist yet.
    import subprocess

    result = subprocess.run(
        ["python3", "-m", "alembic", "-c", "alembic.ini", "upgrade", "head", "--sql"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr

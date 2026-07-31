# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 22:05:00

"""PowerSync service smoke tests.

Run after `make infra-up`. If no explicit PowerSync URL is set and the local
service is not reachable, the test is skipped for sandbox compatibility. Set
`PARENTING_POWERSYNC_STRICT=1` to force a failure on unreachable service.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from server.app.sync.service.powersync_probe import probe_powersync

pytestmark = pytest.mark.integration


def _powersync_url() -> str | None:
    return os.getenv("PARENTING_POWERSYNC__URL") or os.getenv("PARENTING_POWERSYNC_URL")


def test_powersync_liveness_probe() -> None:
    explicit_url = _powersync_url()
    result = probe_powersync(explicit_url, timeout_seconds=2.0)
    if not result.ok and not explicit_url and os.getenv("PARENTING_POWERSYNC_STRICT") != "1":
        pytest.skip(f"PowerSync not reachable at {result.base_url}: {result.liveness.error}")

    assert result.liveness.ok, result.liveness.error


def test_powersync_sync_configs_include_core_tables() -> None:
    deploy_config = yaml.safe_load(Path("deploy/powersync/sync-config.yaml").read_text())
    app_config = yaml.safe_load(Path("server/app/sync/infra/powersync_config.yaml").read_text())

    deploy_text = str(deploy_config)
    app_text = str(app_config)

    assert "observation_event" in deploy_text
    assert "observation_event" in app_text
    assert "derived_baby_state" in app_text
    assert "is_deleted" in deploy_text

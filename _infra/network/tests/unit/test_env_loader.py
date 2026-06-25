"""Unit tests for local .env loader."""

import os
from pathlib import Path

from _infra.network.core.secrets import load_local_env_files


def test_load_local_env_files_does_not_override_existing(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "models.yaml").write_text("models: {}", encoding="utf-8")
    (tmp_path / ".env").write_text(
        'TAVILY_API_KEY="from_file"\nSERPER_API_KEY=serper_file\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("TAVILY_API_KEY", "already_exported")
    monkeypatch.delenv("SERPER_API_KEY", raising=False)

    loaded = load_local_env_files(tmp_path)

    assert loaded == [tmp_path / ".env"]
    assert os.environ["TAVILY_API_KEY"] == "already_exported"
    assert os.environ["SERPER_API_KEY"] == "serper_file"

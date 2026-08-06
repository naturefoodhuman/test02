# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-05 13:20:00

"""FORGE environment config audit tests."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.diagnostics.env_config_audit import audit_env_files  # noqa: E402


def test_env_audit_detects_markdown_polluted_url(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        'FORGE_USE_NIM_PROXY=1\nNIM_PROXY_BASE_URL="[http://127.0.0.1:4010/v1](x)"\n',
        encoding="utf-8",
    )
    (tmp_path / "_infra").mkdir()
    report = audit_env_files(tmp_path)

    assert report.status == "fail"
    assert any(issue.key == "NIM_PROXY_BASE_URL" for issue in report.issues)
    assert any(issue.key == "NVIDIA_API_KEY_1" for issue in report.issues)


def test_env_audit_detects_duplicate_conflicts(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("FORGE_REMOTE_MAX_CONCURRENCY=5\n", encoding="utf-8")
    (tmp_path / "_infra").mkdir()
    (tmp_path / "_infra" / ".env").write_text(
        "FORGE_REMOTE_MAX_CONCURRENCY=2\n",
        encoding="utf-8",
    )

    report = audit_env_files(tmp_path)

    assert report.status == "fail"
    assert "FORGE_REMOTE_MAX_CONCURRENCY" in report.duplicate_keys


def test_env_audit_passes_for_clean_root_env(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "FORGE_USE_NIM_PROXY=1",
                "NIM_PROXY_BASE_URL=http://127.0.0.1:4010/v1",
                "NVIDIA_API_KEY_1=secret-one",
                "NIM_PROXY_PER_KEY_RPM=35",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "_infra").mkdir()

    report = audit_env_files(tmp_path)

    assert report.status == "pass"
    assert report.effective_values["NVIDIA_API_KEY_1"].startswith("<redacted:")

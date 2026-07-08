# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 22:08:00


"""Bootstrap structure tests for APC-T001."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    "README.md",
    "Makefile",
    "pyproject.toml",
    ".env.example",
    ".gitignore",
    "docs/ARCHITECTURE_FINAL.md",
    "docs/ENGINEERING_DESIGN.md",
    "docs/TASK_BACKLOG.md",
    "docs/PROJECT_STATE.md",
    "docs/DEV_LOG.md",
    "docs/CHANGELOG.md",
    "docs/HANDOFF.md",
    "docs/ADR/ADR-001-project-bootstrap.md",
    "server/app/__init__.py",
]


REQUIRED_DIRS = [
    "android",
    "firmware/esp32c6",
    "config",
    "deploy",
    "runtime",
]


def test_required_bootstrap_files_exist() -> None:
    missing = [rel for rel in REQUIRED_FILES if not (PROJECT_ROOT / rel).is_file()]
    assert missing == []


def test_required_bootstrap_directories_exist() -> None:
    missing = [rel for rel in REQUIRED_DIRS if not (PROJECT_ROOT / rel).is_dir()]
    assert missing == []


def test_project_docs_use_actual_directory_casing() -> None:
    expected = "projects/AI-Parenting-Copilot/"
    for rel in ["docs/ARCHITECTURE_FINAL.md", "docs/ENGINEERING_DESIGN.md"]:
        assert expected in (PROJECT_ROOT / rel).read_text(encoding="utf-8")

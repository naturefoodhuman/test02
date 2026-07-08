# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 05:45:00

"""Ensure local development dependencies are installed for Makefile targets.

This script intentionally uses the current interpreter, so it works with the user's
active project/factory virtualenv. It installs the project in editable mode with
`dev` extras only when required imports or command modules are missing.
"""

from __future__ import annotations

import importlib.util
import os
import site
import stat
import subprocess
import sys
import sysconfig
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_MODULES = {
    "alembic": "alembic",
    "fastapi": "fastapi",
    "httpx": "httpx",
    "mypy": "mypy",
    "opentelemetry": "opentelemetry-api",
    "prometheus_client": "prometheus-client",
    "pydantic": "pydantic",
    "pydantic_settings": "pydantic-settings",
    "pytest": "pytest",
    "pytest_asyncio": "pytest-asyncio",
    "ruff": "ruff",
    "sqlalchemy": "SQLAlchemy",
    "structlog": "structlog",
    "ulid": "python-ulid",
    "uvicorn": "uvicorn[standard]",
    "yaml": "PyYAML",
}


def missing_modules() -> list[str]:
    """Return import module names missing from the active interpreter."""

    missing: list[str] = []
    for module_name in REQUIRED_MODULES:
        if importlib.util.find_spec(module_name) is None:
            missing.append(module_name)
    return missing


def install_dev_dependencies(missing: list[str]) -> None:
    """Install project runtime + dev dependencies into the active environment."""

    packages = sorted({REQUIRED_MODULES[name] for name in missing})
    print(
        "Installing missing AI Parenting Copilot dev dependencies: " + ", ".join(packages),
        file=sys.stderr,
    )
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
        cwd=PROJECT_ROOT,
    )


def ensure_ruff_executable() -> None:
    """Fix occasional non-executable ruff script mode in restored sandboxes."""

    script_name = "ruff.exe" if os.name == "nt" else "ruff"
    candidates = [
        Path(sysconfig.get_path("scripts")) / script_name,
        Path(site.getuserbase()) / "bin" / script_name,
    ]
    for script_path in candidates:
        if script_path.exists():
            mode = script_path.stat().st_mode
            script_path.chmod(mode | stat.S_IXUSR)


def command_module_works(module_name: str) -> bool:
    """Return True if `python -m <module> --version` exits successfully."""

    try:
        subprocess.check_call(
            [sys.executable, "-m", module_name, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return False
    return True


def main() -> None:
    ensure_ruff_executable()
    missing = missing_modules()
    if missing:
        install_dev_dependencies(missing)
    ensure_ruff_executable()
    still_missing = missing_modules()
    if still_missing:
        raise SystemExit(f"Missing modules after install: {still_missing}")
    broken_commands = [name for name in ("ruff", "mypy") if not command_module_works(name)]
    if broken_commands:
        install_dev_dependencies(broken_commands)
        ensure_ruff_executable()
    broken_commands = [name for name in ("ruff", "mypy") if not command_module_works(name)]
    if broken_commands:
        raise SystemExit(f"Command modules unavailable after install: {broken_commands}")


if __name__ == "__main__":
    main()

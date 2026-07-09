# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 06:40:00


"""Ensure local development dependencies are installed for Makefile targets.

Works with regular venvs and uv-created pipless venvs. Installation is attempted
using, in order: current interpreter pip, ensurepip+pip, and `uv pip install`.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import site
import stat
import subprocess
import sys
import sysconfig
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_MODULES = {
    "alembic": "alembic",
    "cryptography": "cryptography",
    "fastapi": "fastapi",
    "httpx": "httpx",
    "mypy": "mypy",
    "opentelemetry": "opentelemetry-api",
    "PIL": "Pillow",
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


def _run(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def missing_modules() -> list[str]:
    return [name for name in REQUIRED_MODULES if importlib.util.find_spec(name) is None]


def python_pip_available() -> bool:
    return _run([sys.executable, "-m", "pip", "--version"]).returncode == 0


def try_bootstrap_pip() -> bool:
    if python_pip_available():
        return True
    result = _run([sys.executable, "-m", "ensurepip", "--upgrade"])
    if result.returncode != 0:
        return False
    return python_pip_available()


def install_with_current_pip() -> bool:
    if not try_bootstrap_pip():
        return False
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
        cwd=PROJECT_ROOT,
    )
    return True


def install_with_uv() -> bool:
    uv = shutil.which("uv")
    if not uv:
        return False
    subprocess.check_call(
        [uv, "pip", "install", "--python", sys.executable, "-e", ".[dev]"],
        cwd=PROJECT_ROOT,
    )
    return True


def install_dev_dependencies(missing: list[str]) -> None:
    packages = sorted({REQUIRED_MODULES[name] for name in missing})
    print(
        "Installing missing AI Parenting Copilot dev dependencies: " + ", ".join(packages),
        file=sys.stderr,
    )
    # The factory environment is uv-first and may intentionally use pipless venvs.
    # Prefer `uv pip` when available; only fall back to interpreter pip/ensurepip when uv
    # is absent so the Makefile still works in generic Python environments.
    if install_with_uv():
        return
    if install_with_current_pip():
        return
    raise SystemExit(
        "Cannot install dev dependencies: uv is not available, and current Python pip/"
        "ensurepip failed. Install uv or run `uv pip install --python <venv-python> -e .[dev]`."
    )


def ensure_script_executable(script_name: str) -> None:
    candidates = [
        Path(sysconfig.get_path("scripts")) / script_name,
        Path(site.getuserbase()) / "bin" / script_name,
    ]
    for script_path in candidates:
        if script_path.exists():
            script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR)


def command_module_works(module_name: str) -> bool:
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
    ensure_script_executable("ruff.exe" if os.name == "nt" else "ruff")
    missing = missing_modules()
    if missing:
        install_dev_dependencies(missing)
    ensure_script_executable("ruff.exe" if os.name == "nt" else "ruff")
    still_missing = missing_modules()
    if still_missing:
        raise SystemExit(f"Missing modules after install: {still_missing}")
    broken_commands = [name for name in ("ruff", "mypy") if not command_module_works(name)]
    if broken_commands:
        install_dev_dependencies(broken_commands)
        ensure_script_executable("ruff.exe" if os.name == "nt" else "ruff")
    broken_commands = [name for name in ("ruff", "mypy") if not command_module_works(name)]
    if broken_commands:
        raise SystemExit(f"Command modules unavailable after install: {broken_commands}")


if __name__ == "__main__":
    main()

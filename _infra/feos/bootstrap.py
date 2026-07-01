# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""FEOS bootstrap entrypoint.

Thin wrapper around `config_loader.bootstrap_feos` reserved for later service
wiring. FEOS-002 intentionally does not construct business services.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config_loader import FEOSBootstrapContext, bootstrap_feos as _bootstrap_feos


def bootstrap_feos(
    project_root: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
    create_home: bool = False,
) -> FEOSBootstrapContext:
    return _bootstrap_feos(project_root=project_root, cli_overrides=cli_overrides, create_home=create_home)

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""FEOS bootstrap entrypoint and dependency wiring."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .case_manager import CaseService
from .config_loader import FEOSConfig, bootstrap_feos as _load_bootstrap
from .facade import FEOSFacade
from .repositories import CaseRepository, TimelineRepository
from .storage import FEOSWorkspace


@dataclass
class FEOSRuntimeContext:
    project_root: Path
    config: FEOSConfig
    feos_home: Path
    workspace: FEOSWorkspace
    case_repository: CaseRepository
    timeline_repository: TimelineRepository
    case_service: CaseService
    facade: FEOSFacade


def bootstrap_feos(
    project_root: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
    create_home: bool = False,
) -> FEOSRuntimeContext:
    base = _load_bootstrap(project_root=project_root, cli_overrides=cli_overrides, create_home=create_home)
    workspace = FEOSWorkspace(base.feos_home)
    if create_home:
        workspace.ensure_initialized()
    case_repo = CaseRepository(workspace)
    timeline_repo = TimelineRepository(workspace)
    case_service = CaseService(case_repo, timeline_repo)
    facade = FEOSFacade(case_service)
    return FEOSRuntimeContext(
        project_root=base.project_root,
        config=base.config,
        feos_home=base.feos_home,
        workspace=workspace,
        case_repository=case_repo,
        timeline_repository=timeline_repo,
        case_service=case_service,
        facade=facade,
    )

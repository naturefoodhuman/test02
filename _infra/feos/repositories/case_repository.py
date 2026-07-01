# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""File-system repository for EscalationCase."""

from __future__ import annotations

from pathlib import Path

from _infra.feos.errors import FEOSStorageError
from _infra.feos.models import EscalationCase
from _infra.feos.storage import FEOSWorkspace, read_yaml, write_yaml


class CaseRepository:
    def __init__(self, workspace: FEOSWorkspace):
        self.workspace = workspace

    def case_path(self, case_id: str) -> Path:
        return self.workspace.case_dir(case_id) / "case.yaml"

    def save(self, case: EscalationCase) -> Path:
        path = self.case_path(case.id)
        write_yaml(path, case.to_dict())
        if path.parent.name != case.id:
            raise FEOSStorageError("case directory must equal case id")
        return path

    def get(self, case_id: str) -> EscalationCase:
        path = self.case_path(case_id)
        try:
            data = read_yaml(path)
            case = EscalationCase(**data)
        except Exception as exc:
            raise FEOSStorageError(f"failed to load case {case_id}: {exc}") from exc
        if case.id != case_id:
            raise FEOSStorageError(f"case id mismatch: directory={case_id}, file={case.id}")
        return case

    def list(self) -> list[EscalationCase]:
        cases_root = self.workspace.root / "cases"
        if not cases_root.exists():
            return []
        out: list[EscalationCase] = []
        for path in sorted(cases_root.glob("*/case.yaml")):
            out.append(self.get(path.parent.name))
        return out

# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""FEOS public internal facade."""

from __future__ import annotations

from _infra.feos.case_manager import CaseService, CreateCaseInput
from _infra.feos.models import EscalationCase, ServiceResult


class FEOSFacade:
    def __init__(self, case_service: CaseService):
        self.case_service = case_service

    def create_case(self, input: CreateCaseInput) -> ServiceResult[EscalationCase]:
        try:
            return ServiceResult.success(self.case_service.create_case(input))
        except Exception as exc:
            return ServiceResult.failure(str(exc))

    def get_case(self, case_id: str) -> ServiceResult[EscalationCase]:
        try:
            return ServiceResult.success(self.case_service.get_case(case_id))
        except Exception as exc:
            return ServiceResult.failure(str(exc))

    def list_cases(self) -> ServiceResult[list[EscalationCase]]:
        try:
            return ServiceResult.success(self.case_service.list_cases())
        except Exception as exc:
            return ServiceResult.failure(str(exc))

    def not_implemented(self, operation: str) -> ServiceResult[None]:
        return ServiceResult.failure(f"operation not implemented: {operation}")

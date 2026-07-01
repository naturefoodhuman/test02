# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.execution import ExecutionService
from _infra.feos.ingestion import ResponseIngestionService
from _infra.feos.repositories import ExecutionRepository, ResponseRepository, VerificationRepository
from _infra.feos.storage import FEOSWorkspace
from _infra.feos.verification import VerificationService


class ResponseProcessingWorkflow:
    def __init__(self, workspace: FEOSWorkspace):
        self.workspace = workspace

    def import_parse_verify_plan(self, case_id: str, raw_response: str):
        ingestion = ResponseIngestionService(ResponseRepository(self.workspace))
        response = ingestion.import_text(case_id, raw_response)
        parsed = ingestion.parse_response(response)
        verification = VerificationService(VerificationRepository(self.workspace)).verify(parsed)
        plan = ExecutionService(ExecutionRepository(self.workspace)).create_plan(parsed, verification)
        return {"response": response, "parsed": parsed, "verification": verification, "plan": plan}

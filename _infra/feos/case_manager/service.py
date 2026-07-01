# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Case lifecycle service."""

from __future__ import annotations

from dataclasses import dataclass

from _infra.feos.models import CaseAudit, CaseProblem, CaseStatus, EscalationCase, TimelineEvent
from _infra.feos.models.ids import FEOSIdGenerator, utc_now_iso
from _infra.feos.repositories import CaseRepository, TimelineRepository

from .state_machine import CaseStateMachine


@dataclass
class CreateCaseInput:
    title: str
    user_goal: str
    expected_behavior: str | None = None
    actual_behavior: str | None = None
    task_id: str | None = None
    actor: str = "human"


class CaseService:
    def __init__(self, case_repository: CaseRepository, timeline_repository: TimelineRepository, id_generator: FEOSIdGenerator | None = None):
        self.case_repository = case_repository
        self.timeline_repository = timeline_repository
        self.ids = id_generator or FEOSIdGenerator()
        self.state_machine = CaseStateMachine()

    def create_case(self, data: CreateCaseInput) -> EscalationCase:
        case = EscalationCase(
            id=self.ids.case_id(),
            title=data.title,
            task_id=data.task_id,
            status=CaseStatus.CREATED,
            problem=CaseProblem(
                user_goal=data.user_goal,
                expected_behavior=data.expected_behavior,
                actual_behavior=data.actual_behavior,
            ),
            audit=CaseAudit(created_by=data.actor, last_transition_by=data.actor),
        )
        self.case_repository.save(case)
        self.timeline_repository.append(
            TimelineEvent(id=self.ids.next("evt"), case_id=case.id, type="case_created", actor=data.actor, summary=data.title)
        )
        return case

    def get_case(self, case_id: str) -> EscalationCase:
        return self.case_repository.get(case_id)

    def list_cases(self) -> list[EscalationCase]:
        return self.case_repository.list()

    def transition_case(self, case_id: str, target: CaseStatus | str, actor: str = "human", context: dict | None = None) -> EscalationCase:
        case = self.case_repository.get(case_id)
        self.state_machine.validate(case.status, target, context=context)
        old_status = str(case.status)
        case.status = CaseStatus(target)
        case.updated_at = utc_now_iso()
        case.audit.last_transition_by = actor
        self.case_repository.save(case)
        self.timeline_repository.append(
            TimelineEvent(
                id=self.ids.next("evt"),
                case_id=case.id,
                type="case_transition",
                actor=actor,
                summary=f"{old_status} -> {case.status}",
                data={"from": old_status, "to": str(case.status)},
            )
        )
        return case

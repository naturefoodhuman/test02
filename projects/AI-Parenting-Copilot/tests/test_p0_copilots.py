# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 05:10:00


"""APC-T030 P0 Copilot wrapper tests."""

from __future__ import annotations

import pytest

from server.app.copilots.base import CopilotRegistry, CopilotRequest
from server.app.copilots.family_memory import FamilyMemoryCopilot
from server.app.copilots.growth_milestone import GrowthMilestoneCopilot
from server.app.copilots.medication_safety import MedicationSafetyCopilot
from server.app.copilots.proactive_copilot import ProactiveCopilot
from server.app.copilots.vaccine_planner import VaccinePlannerCopilot
from server.app.memory import MemorySnapshot
from server.app.orchestrator.orchestrator import Orchestrator, OrchestratorRequest


@pytest.mark.asyncio
async def test_vaccine_and_growth_copilots_delegate_to_rule_modules() -> None:
    memory = MemorySnapshot(hard_facts={"birth_date": "2026-07-09", "sex": "male", "age_months": 3})
    vaccine = await VaccinePlannerCopilot().handle(
        CopilotRequest(
            text="疫苗计划",
            intent="vaccine",
            context={"rule_input": {"as_of": "2026-07-09"}},
        ),
        memory,
    )
    growth = await GrowthMilestoneCopilot().handle(
        CopilotRequest(
            text="成长曲线",
            intent="growth",
            context={"rule_input": {"metric": "weight_kg", "value": 6.4}},
        ),
        memory,
    )

    assert vaccine.payload["rule_result"]["reason_code"] == "vaccine_plan_generated"
    assert growth.payload["rule_result"]["outputs"]["percentile_band"] == "p50"
    assert vaccine.evidence and growth.evidence


@pytest.mark.asyncio
async def test_medication_copilot_uses_rule_engine_source() -> None:
    response = await MedicationSafetyCopilot().handle(
        CopilotRequest(
            text="用药",
            intent="medication",
            context={
                "rule_input": {
                    "medication_key": "acetaminophen",
                    "baby_age_months": 4,
                    "weight_kg": 6,
                    "concentration_mg_per_ml": 32,
                }
            },
        ),
        MemorySnapshot(),
    )

    assert response.payload["source"] == "rule_engine"
    assert response.payload["rule_result"]["outputs"]["dose_ml"] > 0
    assert response.requires_confirmation is True


@pytest.mark.asyncio
async def test_family_memory_and_proactive_shells_are_structured_and_safe() -> None:
    family_memory = await FamilyMemoryCopilot().handle(
        CopilotRequest(
            text="宝宝喜欢白噪音",
            intent="family_memory",
            family_id="family-1",
            context={"key": "sleep.preference"},
        ),
        MemorySnapshot(family_id="family-1"),
    )
    proactive = await ProactiveCopilot().handle(
        CopilotRequest(text="提醒", intent="proactive"),
        MemorySnapshot(short_context={"last_feeding_minutes": 120}),
    )

    assert family_memory.payload["memory_update"]["key"] == "sleep.preference"
    assert family_memory.requires_confirmation is True
    assert proactive.payload["reminder_candidates"][0]["alert_level"] is None


@pytest.mark.asyncio
async def test_orchestrator_can_route_explicit_p0_copilot_intent() -> None:
    response = await Orchestrator().handle(
        OrchestratorRequest(
            text="疫苗计划",
            intent="vaccine",
            baby_id="baby-1",
            context={"rule_input": {"birth_date": "2026-07-09", "as_of": "2026-07-09"}},
        )
    )

    assert response.intent == "vaccine"
    assert response.copilot_response is not None
    assert response.copilot_response.copilot == "vaccine_planner"


def test_registry_contains_p0_copilots() -> None:
    registry = CopilotRegistry()
    for copilot in [
        ProactiveCopilot(),
        FamilyMemoryCopilot(),
        VaccinePlannerCopilot(),
        GrowthMilestoneCopilot(),
        MedicationSafetyCopilot(),
    ]:
        registry.register(copilot)

    assert registry.names() == [
        "family_memory",
        "growth_milestone",
        "medication_safety",
        "proactive",
        "vaccine_planner",
    ]


@pytest.mark.asyncio
async def test_rule_copilots_load_rule_packs_from_absolute_project_root(monkeypatch) -> None:
    from pathlib import Path

    monkeypatch.chdir(Path(__file__).resolve().parents[3])
    response = await VaccinePlannerCopilot().handle(
        CopilotRequest(
            text="疫苗计划",
            intent="vaccine",
            context={"rule_input": {"birth_date": "2026-07-09", "as_of": "2026-07-09"}},
        ),
        MemorySnapshot(),
    )

    assert response.payload["rule_result"]["reason_code"] == "vaccine_plan_generated"

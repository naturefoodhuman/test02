# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 23:12:00

"""APC-T019 rules admin API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.app.main import create_app
from server.app.settings import Settings


def test_rules_validate_and_admin_activate_flow() -> None:
    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        validate = client.get("/api/v1/rules/validate")
        assert validate.status_code == 200
        assert validate.json()["count"] >= 4

        denied = client.post(
            "/api/v1/rules/activate",
            json={"path": "config/rules/medication/base.yaml"},
        )
        assert denied.status_code == 403

        activated = client.post(
            "/api/v1/rules/activate",
            headers={"x-role": "Admin"},
            json={"path": "config/rules/medication/base.yaml"},
        )
        assert activated.status_code == 200
        assert activated.json()["activated"]["policy_type"] == "medication"

    assert app.state.evidence_policy_repo.get_current("medication") is not None
    assert app.state.audit_sink.records[-1].action == "rule.activate"


def test_rule_evaluate_api_covers_p0_domains() -> None:
    app = create_app(Settings(env="test"))
    with TestClient(app) as client:
        medication = client.post(
            "/api/v1/rules/evaluate/medication",
            json={
                "payload": {
                    "medication_key": "acetaminophen",
                    "baby_age_months": 4,
                    "weight_kg": 6,
                    "concentration_mg_per_ml": 32,
                }
            },
        )
        triage = client.post(
            "/api/v1/rules/evaluate/triage",
            json={"payload": {"baby_age_months": 2, "temperature_c": 38.2}},
        )
        thresholds = client.post(
            "/api/v1/rules/evaluate/thresholds",
            json={"payload": {"consecutive_days": 2, "deviation_percent": 25}},
        )
        vaccine = client.post(
            "/api/v1/rules/evaluate/vaccine",
            json={"payload": {"birth_date": "2026-07-09", "as_of": "2026-07-09"}},
        )
        growth = client.post(
            "/api/v1/rules/evaluate/growth",
            json={"payload": {"sex": "male", "age_months": 3, "metric": "weight_kg", "value": 6.4}},
        )

    assert medication.status_code == 200
    assert medication.json()["result"]["outputs"]["dose_ml"] > 0
    assert triage.json()["result"]["outputs"]["alert_level"] == "red"
    assert thresholds.json()["result"]["outputs"]["alert_level"] == "yellow"
    assert vaccine.json()["result"]["reason_code"] == "vaccine_plan_generated"
    assert growth.json()["result"]["outputs"]["percentile_band"] == "p50"

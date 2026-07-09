# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 13:40:00

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

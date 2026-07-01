# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.bootstrap import bootstrap_feos
from _infra.feos.case_manager import CreateCaseInput


def test_bootstrap_returns_facade_and_can_create_case(tmp_path, monkeypatch):
    monkeypatch.setenv("FEOS_HOME", str(tmp_path / "feos"))
    ctx = bootstrap_feos(create_home=True)
    result = ctx.facade.create_case(CreateCaseInput(title="T", user_goal="debug"))
    assert result.ok is True
    assert result.value.id.startswith("case_")


def test_facade_not_implemented_result(tmp_path, monkeypatch):
    monkeypatch.setenv("FEOS_HOME", str(tmp_path / "feos"))
    ctx = bootstrap_feos(create_home=True)
    result = ctx.facade.not_implemented("future")
    assert result.ok is False
    assert "not implemented" in result.errors[0]

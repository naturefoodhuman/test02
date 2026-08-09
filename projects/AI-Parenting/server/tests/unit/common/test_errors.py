# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
"""异常层次与错误信封单元测试（APC-T002 测试要求：异常映射）。"""

from __future__ import annotations

from server.app.common.errors import (
    ConflictError,
    DomainError,
    ErrorEnvelope,
    ForbiddenError,
    InfrastructureError,
    NotFoundError,
    RuleViolationError,
    UnauthorizedError,
    ValidationError,
)


def test_error_envelope_has_required_fields():
    env = ErrorEnvelope(code="PARENTING.X", message="m", trace_id="01KZ" + "0" * 22)
    assert env.code == "PARENTING.X"
    assert env.message == "m"
    assert env.evidence is None
    assert env.trace_id == "01KZ" + "0" * 22


def test_domain_error_generates_trace_id():
    e = NotFoundError("not found")
    assert e.trace_id  # 自动生成
    assert len(e.trace_id) == 26


def test_domain_error_uses_provided_trace_id():
    tid = "01KZ" + "0" * 22
    e = NotFoundError("x", trace_id=tid)
    assert e.trace_id == tid


def test_to_envelope_roundtrip():
    e = NotFoundError("baby not found", evidence={"baby_id": "01KZ"})
    env = e.to_envelope()
    assert env.code == "PARENTING.NOT_FOUND"
    assert env.message == "baby not found"
    assert env.evidence == {"baby_id": "01KZ"}
    assert len(env.trace_id) == 26


def test_http_status_mapping():
    cases = [
        (ValidationError("x"), 422),
        (NotFoundError("x"), 404),
        (ConflictError("x"), 409),
        (UnauthorizedError("x"), 401),
        (ForbiddenError("x"), 403),
        (RuleViolationError("x"), 422),
        (InfrastructureError("x"), 503),
    ]
    for exc, status in cases:
        assert exc.http_status == status, exc


def test_error_codes_are_namespaced():
    for exc_cls in [
        ValidationError,
        NotFoundError,
        ConflictError,
        UnauthorizedError,
        ForbiddenError,
        RuleViolationError,
        InfrastructureError,
    ]:
        assert exc_cls.code.startswith("PARENTING."), exc_cls


def test_domain_error_is_exception_subclass():
    e = NotFoundError("x")
    assert isinstance(e, DomainError)
    assert isinstance(e, Exception)

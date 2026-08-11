# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
# 更新时间（北京时间）：2026-08-10 对齐 ENGINEERING_DESIGN §9.1 类名与 http_status。
"""异常层次与错误信封单元测试（APC-T002 测试要求：异常映射）。

类名与 http_status 严格对齐 ENGINEERING_DESIGN §9.1。
"""

from __future__ import annotations

from server.app.common.errors import (
    AuthError,
    ConflictError,
    DoseInterceptError,
    ErrorEnvelope,
    ForbiddenError,
    NotFoundError,
    ParentingError,
    RuleViolation,
    UpstreamTimeout,
    UpstreamUnavailable,
    ValidationError,
)


def test_error_envelope_has_required_fields():
    env = ErrorEnvelope(code="PARENTING.X", message="m", trace_id="01KZ" + "0" * 22)
    assert env.code == "PARENTING.X"
    assert env.message == "m"
    assert env.evidence is None
    assert env.trace_id == "01KZ" + "0" * 22


def test_parenting_error_generates_trace_id():
    e = NotFoundError("not found")
    assert e.trace_id  # 自动生成
    assert len(e.trace_id) == 26


def test_parenting_error_uses_provided_trace_id():
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
    # 严格对齐 ENGINEERING_DESIGN §9.1 的 http_status。
    cases = [
        (ValidationError("x"), 400),
        (AuthError("x"), 401),
        (ForbiddenError("x"), 403),
        (NotFoundError("x"), 404),
        (ConflictError("x"), 409),
        (RuleViolation("x"), 422),
        (DoseInterceptError("x"), 422),
        (UpstreamUnavailable("x"), 503),
        (UpstreamTimeout("x"), 504),
    ]
    for exc, status in cases:
        assert exc.http_status == status, exc


def test_error_codes_are_namespaced():
    for exc_cls in [
        ValidationError,
        AuthError,
        ForbiddenError,
        NotFoundError,
        ConflictError,
        RuleViolation,
        DoseInterceptError,
        UpstreamUnavailable,
        UpstreamTimeout,
    ]:
        assert exc_cls.code.startswith("PARENTING."), exc_cls


def test_parenting_error_is_exception_subclass():
    e = NotFoundError("x")
    assert isinstance(e, ParentingError)
    assert isinstance(e, Exception)


def test_forbidden_error_is_auth_error_subclass():
    # §9.1：AuthError 承担 401/403；ForbiddenError 为其 403 子类。
    assert issubclass(ForbiddenError, AuthError)
    e = ForbiddenError("no perm")
    assert isinstance(e, AuthError)
    assert e.http_status == 403


def test_dose_intercept_is_rule_violation_subclass():
    # §9.1：DoseInterceptError(RuleViolation) 剂量拦截。
    assert issubclass(DoseInterceptError, RuleViolation)
    e = DoseInterceptError("dose over threshold")
    assert isinstance(e, RuleViolation)
    assert e.http_status == 422
    assert e.code == "PARENTING.DOSE_INTERCEPT"

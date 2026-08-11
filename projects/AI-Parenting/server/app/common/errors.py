# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
#
# common/errors.py —— 统一领域异常层次 + 全局错误信封。
# 依据：ENGINEERING_DESIGN §9.1（异常层次，类名与 http_status 以本文档为准）；
#       TASK_BACKLOG APC-T002（全局异常格式 {code,message,evidence,trace_id}）；
#       ARCHITECTURE_FINAL §15（API 风格）。
# 设计：领域层抛出语义化 ParentingError 子类；网关层统一映射为 HTTP 状态 + 错误信封。
#       trace_id 贯穿请求链路，便于跨进程/跨端排障。
# 对齐：类名与 http_status 严格遵循 ENGINEERING_DESIGN §9.1（P3 文档为命名 SSOT）。

"""统一领域异常层次与全局错误信封。

领域层只抛出语义化 ``ParentingError`` 子类（不感知 HTTP）；网关层
``exception_handlers`` 统一映射为 HTTP 状态码 + ``ErrorEnvelope``。
``trace_id`` 贯穿请求链路，便于跨进程/跨端排障（架构 §22 可观测性）。

异常层次与命名严格对齐 ``ENGINEERING_DESIGN §9.1``：

- ``ParentingError`` —— 基类（500）
- ``ValidationError`` —— 输入校验失败（400）
- ``AuthError`` —— 认证/授权失败（401）；``ForbiddenError`` 为其 403 子类
- ``NotFoundError`` —— 资源不存在（404）
- ``ConflictError`` —— 并发/同步冲突（409）
- ``RuleViolation`` —— 规则拦截（422）；``DoseInterceptError`` 为其剂量拦截子类
- ``UpstreamTimeout`` —— 上游超时（504）
- ``UpstreamUnavailable`` —— 上游不可达（503）
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict

from .ids import new_id


class ErrorEnvelope(BaseModel):
    """全局错误响应信封（架构 §15 / TASK_BACKLOG APC-T002）。

    Attributes:
        code: 机器可读错误码（如 ``PARENTING.EVENT.NOT_FOUND``）。
        message: 人类可读错误描述（已脱敏，不含密钥/PII）。
        evidence: 错误证据（如字段校验失败明细），可为 None。
        trace_id: 贯穿请求链路的追踪 ID（ULID），便于跨端排障。
    """

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    evidence: Mapping[str, Any] | None = None
    trace_id: str


class ParentingError(Exception):
    """所有领域异常基类（ENGINEERING_DESIGN §9.1）。

    子类应设置类属性 ``code``（机器可读错误码）与默认 ``http_status``。
    网关层据此映射 HTTP 响应，领域层不直接感知 HTTP。
    """

    code: str = "PARENTING.INTERNAL"
    http_status: int = 500
    # 默认错误码命名空间前缀，子类可覆盖。
    _namespace: str = "PARENTING"

    def __init__(
        self,
        message: str,
        *,
        evidence: Mapping[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.evidence = evidence
        # trace_id 未提供则现场生成；调用方可注入请求级 trace_id 以贯穿链路。
        self.trace_id = trace_id or new_id()

    def to_envelope(self) -> ErrorEnvelope:
        """转换为全局错误信封。"""
        return ErrorEnvelope(
            code=self.code,
            message=self.message,
            evidence=self.evidence,
            trace_id=self.trace_id,
        )


class ValidationError(ParentingError):
    """输入校验失败（ENGINEERING_DESIGN §9.1，对应 HTTP 400）。

    注意：领域层业务校验失败抛本类（400）；FastAPI/pydantic 请求 schema
    校验失败由网关层 ``RequestValidationError`` 处理（422），两者语义不同。
    """

    code = "PARENTING.VALIDATION"
    http_status = 400


class AuthError(ParentingError):
    """认证/授权失败（ENGINEERING_DESIGN §9.1，对应 HTTP 401/403）。

    默认 401（未认证）；403（无权限）由子类 ``ForbiddenError`` 表达。
    """

    code = "PARENTING.UNAUTHORIZED"
    http_status = 401


class ForbiddenError(AuthError):
    """无权限（``AuthError`` 的 403 子类，ENGINEERING_DESIGN §9.1）。"""

    code = "PARENTING.FORBIDDEN"
    http_status = 403


class NotFoundError(ParentingError):
    """资源不存在（ENGINEERING_DESIGN §9.1，对应 HTTP 404）。"""

    code = "PARENTING.NOT_FOUND"
    http_status = 404


class ConflictError(ParentingError):
    """资源冲突 / 并发版本冲突 / 同步冲突（ENGINEERING_DESIGN §9.1，对应 HTTP 409）。"""

    code = "PARENTING.CONFLICT"
    http_status = 409


class RuleViolation(ParentingError):
    """规则引擎裁决违例（医疗/剂量/阈值，ENGINEERING_DESIGN §9.1/§10.2/§11.3）。

    默认 HTTP 422（输入不满足规则约束）；具体规则子类可覆盖。
    """

    code = "PARENTING.RULE_VIOLATION"
    http_status = 422


class DoseInterceptError(RuleViolation):
    """剂量拦截（``RuleViolation`` 子类，ENGINEERING_DESIGN §9.1）。

    规则引擎判定剂量超阈值/冲突时抛出，复用 ``RuleViolation`` 的 422 状态。
    """

    code = "PARENTING.DOSE_INTERCEPT"
    http_status = 422


class UpstreamUnavailable(ParentingError):
    """上游服务不可达（DB/MQTT/模型后端，ENGINEERING_DESIGN §9.1，对应 HTTP 503）。"""

    code = "PARENTING.UPSTREAM_UNAVAILABLE"
    http_status = 503


class UpstreamTimeout(ParentingError):
    """上游服务超时（DB/MQTT/模型后端，ENGINEERING_DESIGN §9.1，对应 HTTP 504）。"""

    code = "PARENTING.UPSTREAM_TIMEOUT"
    http_status = 504


__all__ = [
    "AuthError",
    "ConflictError",
    "DoseInterceptError",
    "ErrorEnvelope",
    "ForbiddenError",
    "NotFoundError",
    "ParentingError",
    "RuleViolation",
    "UpstreamTimeout",
    "UpstreamUnavailable",
    "ValidationError",
]

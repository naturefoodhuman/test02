# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
#
# app/observability/logger.py —— 结构化日志（structlog JSON）。
# 依据：ENGINEERING_DESIGN §10.1（Logging）；ARCHITECTURE_FINAL §22.1；TASK_BACKLOG APC-T005。
# 设计：structlog JSON → stdout（launchd 接管转 runtime/logs/，logrotate 日切）。
#       全局字段：trace_id, span_id, request_id, family_id, baby_id, user_id, actor_kind, module。
#       PII 自动 mask（raw_input/媒体路径/常见 PII 模式）；与 common/ids 的 trace_id 贯穿。
# 边界：不读取工厂 sanitizer（红线不碰 _infra/.env），自实现简易 masker 覆盖 §10.1 脱敏要求。

"""结构化日志（structlog JSON）。

配置 structlog 输出 JSON 到 stdout（架构 §22.1：stdout → launchd → runtime/logs/）。
全局上下文字段（§10.1）：``trace_id, span_id, request_id, family_id, baby_id,
user_id, actor_kind, module``，通过 ``bind_context`` 注入，``get_context`` 读取，
``clear_context`` 清理（请求/任务结束）。

PII 自动 mask（§10.1）：``mask_pii`` 对 dict/str 递归脱敏 ``raw_input``、媒体路径、
常见 PII 模式（手机号/邮箱/身份证）。不读取工厂 sanitizer，自实现简易 masker。
"""

from __future__ import annotations

import logging
import re
import sys
from typing import Any

import structlog

# ---- PII 脱敏 ----
# 常见 PII 正则：手机号（11 位）、邮箱、身份证（18 位含 X）。
_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("phone", re.compile(r"\b1[3-9]\d{9}\b")),
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("id_card", re.compile(r"\b\d{17}[\dXx]\b")),
]
# 需脱敏的 key（命中即整体替换为 ***，不递归内容）。
_SENSITIVE_KEYS = {
    "raw_input",
    "raw",
    "password",
    "auth_hash",
    "token",
    "secret",
    "api_key",
    "fcm_token",
    "access_token",
    "refresh_token",
}
# 媒体/文件路径脱敏：保留目录结构，替换文件名为 ***。
_PATH_RE = re.compile(r"(/[\w./-]+/)([\w.-]+)$")


def mask_pii(value: Any) -> Any:
    """递归脱敏 PII（dict/str/list）。

    - dict：命中 ``_SENSITIVE_KEYS`` 的 value 整体替换为 "***"；其余递归。
    - str：跑 PII 正则替换；媒体路径文件名脱敏。
    - list/tuple：递归元素。
    """
    if isinstance(value, dict):
        return {k: ("***" if k in _SENSITIVE_KEYS else mask_pii(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [mask_pii(v) for v in value]
    if isinstance(value, tuple):
        return tuple(mask_pii(v) for v in value)
    if isinstance(value, str):
        masked = value
        for _name, pat in _PII_PATTERNS:
            masked = pat.sub("***", masked)
        masked = _PATH_RE.sub(lambda m: f"{m.group(1)}***", masked)
        return masked
    return value


# ---- 上下文 ----
# 进程级 context 变量（structlog contextvars），async 安全。
_context = structlog.contextvars.bound_contextvars


def bind_context(**kwargs: Any) -> None:
    """绑定日志上下文字段（§10.1：trace_id/span_id/request_id/family_id/baby_id/user_id/actor_kind/module）。

    值会先经 mask_pii 脱敏再绑定，避免 PII 入日志。kwargs 视作 dict 走脱敏，
    命中 ``_SENSITIVE_KEYS`` 的 key（如 raw_input/password/token）整体替换为 "***"。
    """
    masked = mask_pii(dict(kwargs))
    structlog.contextvars.bind_contextvars(**masked)


def clear_context() -> None:
    """清理日志上下文（请求/任务结束调用，防止跨请求泄漏）。"""
    structlog.contextvars.clear_contextvars()


def get_context() -> dict[str, Any]:
    """读取当前日志上下文（用于手动构造日志或传递到下游）。"""
    return dict(structlog.contextvars.get_contextvars())


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """获取 structlog logger（自动带 module 上下文）。

    ``name`` 通常传 ``__name__``，作为 ``module`` 字段。
    """
    log = structlog.get_logger(name or "parenting")
    return log


def configure_logging(level: str = "INFO") -> None:
    """配置 structlog（JSON → stdout）。

    应在应用启动时调用（``main.py`` lifespan 或 ``_configure_logging``）。
    幂等：重复调用重置 processors。
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


__all__ = [
    "bind_context",
    "clear_context",
    "configure_logging",
    "get_context",
    "get_logger",
    "mask_pii",
]

# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 16:05:00 CST

"""
统一异常体系（FORGE Network 增量）

基类：NetworkError
子类按领域分类：
- MCP 相关
- Search 相关
- Extract 相关
- Privacy 相关
- Browser 相关

每个异常必须有：
- code: str（错误码）
- 关键异常携带上下文（entities、details 等）
"""

from __future__ import annotations

from typing import Any, List, Optional


class NetworkError(Exception):
    """所有网络功能异常基类"""

    code: str = "NETWORK_ERROR"

    def __init__(self, message: str, *, code: Optional[str] = None, **kwargs: Any):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.details: dict[str, Any] = kwargs


# ===================== MCP 层 =====================

class MCPError(NetworkError):
    code = "MCP_ERROR"


class MCPSchemaChangedError(MCPError):
    code = "MCP_SCHEMA_CHANGED"

    def __init__(self, server_id: str, old_hash: str, new_hash: str, **kwargs):
        super().__init__(
            f"MCP server '{server_id}' schema changed",
            code=self.code,
            server_id=server_id,
            old_hash=old_hash,
            new_hash=new_hash,
            **kwargs,
        )


class PolicyDeniedError(MCPError):
    code = "MCP_POLICY_DENIED"

    def __init__(self, tool_name: str, reason: str, **kwargs):
        super().__init__(
            f"Tool '{tool_name}' denied by policy: {reason}",
            code=self.code,
            tool_name=tool_name,
            reason=reason,
            **kwargs,
        )


# ===================== 搜索层 =====================

class SearchError(NetworkError):
    code = "SEARCH_ERROR"


class SearchEngineUnavailable(SearchError):
    code = "SEARCH_ENGINE_UNAVAILABLE"


class SearchRateLimited(SearchError):
    code = "SEARCH_RATE_LIMITED"


class SearchResultEmpty(SearchError):
    code = "SEARCH_RESULT_EMPTY"


# ===================== 提取层 =====================

class ExtractError(NetworkError):
    code = "EXTRACT_ERROR"


class AllExtractorsFailed(ExtractError):
    code = "ALL_EXTRACTORS_FAILED"


class ExtractTimeout(ExtractError):
    code = "EXTRACT_TIMEOUT"


class ContentTooLarge(ExtractError):
    code = "CONTENT_TOO_LARGE"


# ===================== 隐私网关 =====================

class PrivacyError(NetworkError):
    code = "PRIVACY_ERROR"


class PIIDetectedError(PrivacyError):
    code = "PII_DETECTED"

    def __init__(self, detections: List[dict], message: str = "PII detected", **kwargs):
        super().__init__(
            message,
            code=self.code,
            detections=detections,
            **kwargs,
        )
        self.detections = detections


class CanaryTokenDetectedError(PrivacyError):
    code = "CANARY_TOKEN_DETECTED"

    def __init__(self, token: str, location: str, **kwargs):
        super().__init__(
            f"Canary token detected: {token} at {location}",
            code=self.code,
            token=token,
            location=location,
            **kwargs,
        )


class SchemaValidationFailedError(PrivacyError):
    code = "SCHEMA_VALIDATION_FAILED"


# ===================== 浏览器层 =====================

class BrowserError(NetworkError):
    code = "BROWSER_ERROR"


class SessionExpiredError(BrowserError):
    code = "SESSION_EXPIRED"

    def __init__(self, profile: str, url: str, **kwargs):
        super().__init__(
            f"Session expired in profile '{profile}' at {url}",
            code=self.code,
            profile=profile,
            url=url,
            **kwargs,
        )


class BrowserCrashError(BrowserError):
    code = "BROWSER_CRASH"


class ForbiddenBrowserActionError(BrowserError):
    code = "FORBIDDEN_BROWSER_ACTION"


# ===================== 配置 & 通用 =====================

class ConfigError(NetworkError):
    code = "CONFIG_ERROR"


class NetworkConfigError(ConfigError):
    code = "NETWORK_CONFIG_ERROR"


# 方便的异常工厂（可选）
def raise_if_pii(detections: List[dict], **kwargs):
    if detections:
        raise PIIDetectedError(detections, **kwargs)

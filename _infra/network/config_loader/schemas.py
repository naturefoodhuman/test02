# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 15:10:00 CST

"""Network 配置 Pydantic Schemas（FORGE Factory 增量）

严格复用现有 FORGE 配置模式（参考 peer_review.config.schemas）。
不引入新基础设施。
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

# ===================== 搜索层 =====================

class SearXNGConfig(BaseModel):
    base_url: str = "http://127.0.0.1:8080"
    timeout_seconds: int = Field(6, ge=1, le=30)
    max_results: int = Field(20, ge=1, le=100)
    fetch_top_k: int = Field(5, ge=1, le=50)
    max_chars_per_page: int = Field(8000, ge=500, le=20000)
    engines_enabled: list[str] = Field(default_factory=list)
    engines_disabled: list[str] = Field(default_factory=list)

class TavilyFallbackConfig(BaseModel):
    enabled: bool = False
    api_key_env: str = "TAVILY_API_KEY"

class SearchConfig(BaseModel):
    searxng: SearXNGConfig = Field(default_factory=SearXNGConfig)
    fallback_tavily: TavilyFallbackConfig = Field(default_factory=TavilyFallbackConfig)

# ===================== 提取层 =====================

class Crawl4AIConfig(BaseModel):
    base_url: str = "http://127.0.0.1:11235"
    timeout_seconds: int = Field(30, ge=5, le=120)
    js_exec_allowed: bool = False
    screenshot_requires_approval: bool = True
    api_token: Optional[str] = None
    api_token_env: str = "CRAWL4AI_API_TOKEN"

class TrafilaturaConfig(BaseModel):
    enabled: bool = True
    max_size_bytes: int = 1_048_576

class PlaywrightConfig(BaseModel):
    wrapper_script: str = "_infra/network/scripts/run_playwright_action.py"
    allowed_commands: list[str] = Field(default_factory=lambda: ["open", "snapshot", "click", "type", "wait", "close"])

class ExtractConfig(BaseModel):
    crawl4ai: Crawl4AIConfig = Field(default_factory=Crawl4AIConfig)
    trafilatura: TrafilaturaConfig = Field(default_factory=TrafilaturaConfig)
    playwright: PlaywrightConfig = Field(default_factory=PlaywrightConfig)

# ===================== 浏览器层 =====================

class ProfileConfig(BaseModel):
    user_data_dir: str
    blocked_origins: list[str] = Field(default_factory=list)
    remote_debugging_port: Optional[int] = None
    allowed_domains: list[str] = Field(default_factory=list)

class BrowserConfig(BaseModel):
    profiles: dict[str, ProfileConfig] = Field(default_factory=dict)
    session_expiry: dict = Field(default_factory=lambda: {
        "login_page_patterns": ["登录", "Sign in", "CAPTCHA", "验证码", "2FA"]
    })

# ===================== 隐私网关 =====================

class PrivacyGatewayConfig(BaseModel):
    qwen_model: str = "qwen3:8b"
    qwen_base_url: str = "http://127.0.0.1:11434"
    qwen_timeout_seconds: int = Field(30, ge=5, le=120)
    spacy_model: str = "zh_core_web_sm"
    pii_map_db: str = "runtime/pii_map.db"
    pii_map_encryption_key_env: str = "PII_MAP_ENCRYPTION_KEY"
    canary_tokens: list[str] = Field(default_factory=list)
    output_schema_strict: bool = True
    placeholder_format: str = "<<{entity_type}_{index}>>"

# ===================== 本地 RAG =====================

class LocalRAGConfig(BaseModel):
    rag_db: str = "runtime/rag.db"
    embed_model: str = "bge-m3"
    embed_base_url: str = "http://127.0.0.1:11434"
    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 50
    top_k_default: int = 5
    reranker_enabled: bool = False
    reranker_model: Optional[str] = "bge-reranker-v2-m3"

# ===================== MCP Guard =====================

class MCPGuardConfig(BaseModel):
    hash_store: str = "runtime/mcp_hashes.json"
    audit_db: str = "runtime/audit.db"
    policy_config: str = "config/mcp_policy.yaml"
    scan_interval_days: int = 7
    high_risk_tools: list[str] = Field(default_factory=list)
    forbidden_js_patterns: list[str] = Field(default_factory=list)

# ===================== 模式隔离 =====================

class ModeProfile(BaseModel):
    allowed_servers: list[str] = Field(default_factory=list)
    denied_servers: list[str] = Field(default_factory=list)

class ModeProfilesConfig(BaseModel):
    coding: ModeProfile = Field(default_factory=ModeProfile)
    research: ModeProfile = Field(default_factory=ModeProfile)
    private: ModeProfile = Field(default_factory=ModeProfile)

# ===================== 健康检查 =====================

class HealthServiceConfig(BaseModel):
    url: Optional[str] = None
    command: Optional[str] = None
    timeout: int = 5
    optional: bool = False

class HealthCheckConfig(BaseModel):
    services: dict[str, HealthServiceConfig] = Field(default_factory=dict)

# ===================== 根配置 =====================

class NetworkConfig(BaseModel):
    """网络功能总配置（复用现有 FORGE Pydantic 模式）"""
    version: str = "1.0"
    search: SearchConfig = Field(default_factory=SearchConfig)
    extract: ExtractConfig = Field(default_factory=ExtractConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    privacy_gateway: PrivacyGatewayConfig = Field(default_factory=PrivacyGatewayConfig)
    local_rag: LocalRAGConfig = Field(default_factory=LocalRAGConfig)
    mcp_guard: MCPGuardConfig = Field(default_factory=MCPGuardConfig)
    mode_profiles: ModeProfilesConfig = Field(default_factory=ModeProfilesConfig)
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        if not v.startswith("1."):
            raise ValueError("network.yaml 版本必须以 1. 开头")
        return v

    model_config = {
        "extra": "forbid",   # 严格模式，防止配置漂移
        "validate_assignment": True,
    }
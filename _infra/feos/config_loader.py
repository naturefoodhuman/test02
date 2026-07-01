# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""FEOS configuration loader.

Implements FEOS-002:
- defaults -> config/feos.yaml -> .env/_infra.env -> environment -> CLI overrides
- clear config errors
- no new config framework
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

try:
    from _infra.network.core.secrets import load_local_env_files
except Exception:  # pragma: no cover - import fallback for early bootstrap
    def load_local_env_files(project_root: Path | None = None) -> list[Path]:
        return []


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = ROOT / "_infra" / "feos" / "defaults" / "feos.yaml"
PROJECT_CONFIG_PATH = ROOT / "config" / "feos.yaml"


class FEOSConfigError(Exception):
    """Raised when FEOS configuration cannot be loaded or validated."""


class FEOSDefaultsConfig(BaseModel):
    gateway: str = "clipboard"
    provider: str = "chatgpt_web"
    policy_profile: str = "default_strict"
    renderer_profile: str = "generic_markdown"
    token_budget: int = Field(24000, ge=1)


class FEOSDetectorConfig(BaseModel):
    auto_create_case_if_score_above: float = Field(0.70, ge=0.0, le=1.0)
    suggest_case_if_score_above: float = Field(0.50, ge=0.0, le=1.0)
    continue_local_if_score_below: float = Field(0.50, ge=0.0, le=1.0)
    hard_triggers: list[str] = Field(default_factory=list)


class FEOSEvidenceConfig(BaseModel):
    enabled_collectors: list[str] = Field(default_factory=list)
    required_collectors: list[str] = Field(default_factory=lambda: ["user_input"])
    max_raw_evidence_bytes: int = Field(1_048_576, ge=1)
    max_diff_bytes: int = Field(262_144, ge=1)
    allow_config_files: list[str] = Field(default_factory=list)
    deny_files: list[str] = Field(default_factory=list)


class FEOSContextConfig(BaseModel):
    token_estimator: str = "heuristic"
    default_budget: int = Field(24000, ge=1)
    min_evidence_coverage_rate: float = Field(0.70, ge=0.0, le=1.0)
    compression_order: list[str] = Field(default_factory=list)


class FEOSPolicyConfig(BaseModel):
    privacy_policy_file: str = "config/privacy_policy.yaml"
    canary_tokens_file: str = "config/canary_tokens.yaml"
    default_requires_human_review: bool = True
    external_execution_allowed: bool = False
    keep_original_local_only: bool = True
    keep_redacted_copy: bool = True


class FEOSGatewayItemConfig(BaseModel):
    enabled: bool = False
    copy_command: str | None = None
    paste_command: str | None = None
    audit_level: str | None = None


class FEOSGatewaysConfig(BaseModel):
    clipboard: FEOSGatewayItemConfig = Field(default_factory=lambda: FEOSGatewayItemConfig(enabled=True))
    api: FEOSGatewayItemConfig = Field(default_factory=FEOSGatewayItemConfig)
    mcp: FEOSGatewayItemConfig = Field(default_factory=FEOSGatewayItemConfig)
    browser: FEOSGatewayItemConfig = Field(default_factory=FEOSGatewayItemConfig)
    cloud_agent: FEOSGatewayItemConfig = Field(default_factory=FEOSGatewayItemConfig)


class FEOSRetrievalConfig(BaseModel):
    enabled: bool = True
    prefer_existing_local_rag: bool = True
    fallback: str = "lexical"
    max_results: int = Field(5, ge=0)


class FEOSKnowledgeConfig(BaseModel):
    write_candidates: bool = True
    write_to_knowledge_os: bool = True
    fallback_local_files: bool = True


class FEOSObservabilityConfig(BaseModel):
    log_level: str = "INFO"
    metrics_enabled: bool = True
    audit_enabled: bool = True

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()


class FEOSRootConfig(BaseModel):
    enabled: bool = True
    home: str = ".forge/feos"
    defaults: FEOSDefaultsConfig = Field(default_factory=FEOSDefaultsConfig)
    detector: FEOSDetectorConfig = Field(default_factory=FEOSDetectorConfig)
    evidence: FEOSEvidenceConfig = Field(default_factory=FEOSEvidenceConfig)
    context: FEOSContextConfig = Field(default_factory=FEOSContextConfig)
    policy: FEOSPolicyConfig = Field(default_factory=FEOSPolicyConfig)
    gateways: FEOSGatewaysConfig = Field(default_factory=FEOSGatewaysConfig)
    retrieval: FEOSRetrievalConfig = Field(default_factory=FEOSRetrievalConfig)
    knowledge: FEOSKnowledgeConfig = Field(default_factory=FEOSKnowledgeConfig)
    observability: FEOSObservabilityConfig = Field(default_factory=FEOSObservabilityConfig)


class FEOSConfig(BaseModel):
    feos: FEOSRootConfig = Field(default_factory=FEOSRootConfig)

    @property
    def home_path(self) -> Path:
        return Path(self.feos.home)


class FEOSBootstrapContext(BaseModel):
    project_root: Path
    config: FEOSConfig
    feos_home: Path

    model_config = {"arbitrary_types_allowed": True}


def detect_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "config" / "models.yaml").exists():
            return parent
    return ROOT


def load_yaml_file(path: Path, *, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FEOSConfigError(f"FEOS config file not found: {path}")
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise FEOSConfigError(f"Failed to parse YAML {path}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise FEOSConfigError(f"YAML root must be a mapping: {path}")
    return data


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _env_bool(name: str) -> bool | None:
    raw = os.getenv(name)
    if raw is None:
        return None
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_overrides() -> dict[str, Any]:
    feos: dict[str, Any] = {}
    if os.getenv("FEOS_HOME"):
        feos["home"] = os.environ["FEOS_HOME"]
    if os.getenv("FEOS_LOG_LEVEL"):
        feos.setdefault("observability", {})["log_level"] = os.environ["FEOS_LOG_LEVEL"]
    if os.getenv("FEOS_DEFAULT_PROVIDER"):
        feos.setdefault("defaults", {})["provider"] = os.environ["FEOS_DEFAULT_PROVIDER"]
    if os.getenv("FEOS_DEFAULT_GATEWAY"):
        feos.setdefault("defaults", {})["gateway"] = os.environ["FEOS_DEFAULT_GATEWAY"]
    if os.getenv("FEOS_CLIPBOARD_COPY_CMD"):
        feos.setdefault("gateways", {}).setdefault("clipboard", {})["copy_command"] = os.environ["FEOS_CLIPBOARD_COPY_CMD"]
    if os.getenv("FEOS_CLIPBOARD_PASTE_CMD"):
        feos.setdefault("gateways", {}).setdefault("clipboard", {})["paste_command"] = os.environ["FEOS_CLIPBOARD_PASTE_CMD"]

    for env_name, gateway_name in [
        ("FEOS_ENABLE_API_GATEWAY", "api"),
        ("FEOS_ENABLE_MCP_GATEWAY", "mcp"),
        ("FEOS_ENABLE_BROWSER_GATEWAY", "browser"),
        ("FEOS_ENABLE_CLOUD_AGENT_GATEWAY", "cloud_agent"),
    ]:
        value = _env_bool(env_name)
        if value is not None:
            feos.setdefault("gateways", {}).setdefault(gateway_name, {})["enabled"] = value

    return {"feos": feos} if feos else {}


def normalize_cli_overrides(cli_overrides: dict[str, Any] | None) -> dict[str, Any]:
    if not cli_overrides:
        return {}
    if "feos" in cli_overrides:
        return cli_overrides
    return {"feos": cli_overrides}


def get_project_config_path(project_root: Path) -> Path:
    config_env = os.getenv("FEOS_CONFIG")
    if config_env:
        path = Path(config_env)
        return path if path.is_absolute() else project_root / path
    return project_root / "config" / "feos.yaml"


def load_config(
    project_root: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> FEOSConfig:
    root = detect_project_root(project_root)
    load_local_env_files(root)

    data = load_yaml_file(DEFAULT_CONFIG_PATH)
    data = deep_merge(data, load_yaml_file(get_project_config_path(root), required=False))
    data = deep_merge(data, env_overrides())
    data = deep_merge(data, normalize_cli_overrides(cli_overrides))

    try:
        return FEOSConfig(**data)
    except Exception as exc:
        raise FEOSConfigError(f"FEOS config validation failed: {exc}") from exc


def bootstrap_feos(
    project_root: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
    create_home: bool = False,
) -> FEOSBootstrapContext:
    root = detect_project_root(project_root)
    config = load_config(root, cli_overrides=cli_overrides)
    home = Path(config.feos.home)
    if not home.is_absolute():
        home = root / home
    if create_home:
        home.mkdir(parents=True, exist_ok=True)
    return FEOSBootstrapContext(project_root=root, config=config, feos_home=home)

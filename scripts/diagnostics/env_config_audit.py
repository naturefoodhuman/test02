#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-05 13:20:00

"""Audit FORGE .env and _infra/.env for routing conflicts and URL pollution."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

MARKDOWN_URL_RE = re.compile(r"\[[^\]]*https?://|\]\(https?://")
URL_KEYS = {
    "ANTHROPIC_BASE_URL",
    "OPENAI_BASE_URL",
    "NIM_PROXY_BASE_URL",
    "NETWORK_SEARCH_API_PROXY",
}


@dataclass(frozen=True, slots=True)
class EnvAuditIssue:
    level: str
    key: str
    message: str
    path: str | None = None


@dataclass(frozen=True, slots=True)
class EnvAuditReport:
    status: str
    loaded_files: tuple[str, ...]
    duplicate_keys: dict[str, tuple[str, ...]] = field(default_factory=dict)
    effective_values: dict[str, str] = field(default_factory=dict)
    issues: tuple[EnvAuditIssue, ...] = field(default_factory=tuple)
    recommendations: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip().lstrip("export ").strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def audit_env_files(root: Path | str = ".") -> EnvAuditReport:
    root_path = Path(root)
    paths = [root_path / ".env", root_path / "_infra" / ".env"]
    parsed = {str(path): parse_env_file(path) for path in paths if path.exists()}
    issues: list[EnvAuditIssue] = []
    recommendations: list[str] = []
    duplicate_keys: dict[str, tuple[str, ...]] = {}
    all_keys = sorted({key for values in parsed.values() for key in values})
    for key in all_keys:
        owners = [path for path, values in parsed.items() if key in values]
        if len(owners) > 1:
            vals = {parsed[path][key] for path in owners}
            duplicate_keys[key] = tuple(owners)
            if len(vals) > 1:
                issues.append(
                    EnvAuditIssue(
                        level="error",
                        key=key,
                        message="duplicate key has conflicting values across .env files",
                    )
                )
            else:
                issues.append(
                    EnvAuditIssue(
                        level="warning",
                        key=key,
                        message="duplicate key has same value; prefer single source of truth",
                    )
                )
    root_env = parsed.get(str(root_path / ".env"), {})
    infra_env = parsed.get(str(root_path / "_infra" / ".env"), {})
    effective = dict(infra_env)
    effective.update(root_env)
    for path, values in parsed.items():
        for key, value in values.items():
            if key in URL_KEYS and MARKDOWN_URL_RE.search(value):
                issues.append(
                    EnvAuditIssue(
                        level="error",
                        key=key,
                        path=path,
                        message="URL appears to be Markdown-polluted; use a plain URL",
                    )
                )
    if effective.get("FORGE_USE_NIM_PROXY", "0").lower() in {"1", "true", "yes", "on"}:
        key_count = sum(1 for idx in range(1, 11) if effective.get(f"NVIDIA_API_KEY_{idx}"))
        if key_count == 0:
            issues.append(
                EnvAuditIssue(
                    level="error",
                    key="NVIDIA_API_KEY_1",
                    message="FORGE_USE_NIM_PROXY=1 but no indexed NVIDIA keys are configured",
                )
            )
        if effective.get("NIM_PROXY_BASE_URL") and not effective["NIM_PROXY_BASE_URL"].endswith("/v1"):
            issues.append(
                EnvAuditIssue(
                    level="warning",
                    key="NIM_PROXY_BASE_URL",
                    message="NIM_PROXY_BASE_URL should normally end with /v1",
                )
            )
        rpm = int(effective.get("NIM_PROXY_PER_KEY_RPM", "35") or "35")
        if rpm > 35:
            issues.append(
                EnvAuditIssue(
                    level="warning",
                    key="NIM_PROXY_PER_KEY_RPM",
                    message="free-tier RPM above 35 has little headroom; consider 30-35",
                )
            )
    if "FORGE_REMOTE_MAX_CONCURRENCY" in root_env and "FORGE_REMOTE_MAX_CONCURRENCY" in infra_env:
        recommendations.append(
            "Keep FORGE_REMOTE_MAX_CONCURRENCY in root .env only; _infra/.env should be legacy keys only."
        )
    recommendations.extend(
        [
            "Use root .env as the runtime source of truth for forge-start, smart_proxy, and NIM proxy.",
            "Keep _infra/.env only for legacy LiteLLM credentials if needed; avoid duplicating FORGE_* and NIM_PROXY_* keys there.",
            "Use plain URLs, e.g. http://127.0.0.1:4010/v1, never Markdown links copied from chat.",
        ]
    )
    status = "fail" if any(issue.level == "error" for issue in issues) else "pass"
    return EnvAuditReport(
        status=status,
        loaded_files=tuple(parsed.keys()),
        duplicate_keys=duplicate_keys,
        effective_values={key: _redact_value(key, value) for key, value in sorted(effective.items())},
        issues=tuple(issues),
        recommendations=tuple(recommendations),
    )


def _redact_value(key: str, value: str) -> str:
    if "KEY" in key or "SECRET" in key or "TOKEN" in key or "PASSWORD" in key:
        return f"<redacted:{len(value)}>" if value else ""
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    report = audit_env_files(Path(args.root))
    print(report.to_json())
    if report.status == "fail":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

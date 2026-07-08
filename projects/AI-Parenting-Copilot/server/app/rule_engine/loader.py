# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 02:50:00


"""Rule pack YAML loader and hash validator."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

from server.app.common.errors import ConfigurationError


class RuleDefinition(BaseModel):
    id: str
    description: str = ""
    when: dict[str, Any] = Field(default_factory=dict)
    then: dict[str, Any] = Field(default_factory=dict)


class RulePack(BaseModel):
    policy_type: str
    domain: str
    region: str = "CN"
    version: str
    effective_from: str
    source: str
    rules: list[RuleDefinition] = Field(default_factory=list)
    constants: dict[str, Any] = Field(default_factory=dict)
    hash: str | None = None

    def canonical_payload(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude={"hash"})
        return payload

    def compute_hash(self) -> str:
        encoded = json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def assert_hash_valid(self) -> None:
        if self.hash is not None and self.hash != self.compute_hash():
            raise ConfigurationError(
                "Rule pack hash mismatch",
                evidence={"domain": self.domain, "version": self.version},
            )


def load_rule_pack(path: Path) -> RulePack:
    if not path.exists():
        raise ConfigurationError("Rule pack not found", evidence={"path": str(path)})
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    pack = RulePack.model_validate(raw)
    pack.assert_hash_valid()
    return pack


def load_rule_packs(root: Path) -> list[RulePack]:
    return [load_rule_pack(path) for path in sorted(root.rglob("*.yaml"))]


def validate_rule_packs(root: Path) -> list[RulePack]:
    packs = load_rule_packs(root)
    seen: set[tuple[str, str, str]] = set()
    for pack in packs:
        key = (pack.domain, pack.region, pack.version)
        if key in seen:
            raise ConfigurationError("Duplicate rule pack version", evidence={"key": key})
        seen.add(key)
    return packs


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default="config/rules")
    args = parser.parse_args()
    packs = validate_rule_packs(Path(args.root))
    for pack in packs:
        print(f"{pack.domain}:{pack.region}:{pack.version}:{pack.compute_hash()}")


if __name__ == "__main__":
    main()

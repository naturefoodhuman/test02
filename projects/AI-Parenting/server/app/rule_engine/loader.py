# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/rule_engine/loader.py —— 规则包 YAML 加载器（APC-T018）。
# 依据：ENGINEERING_DESIGN §13.2（YAML → Pydantic → 冻结策略；hash 校验；make rules-validate）；
#       TASK_BACKLOG APC-T018。
# 设计：load_pack(path) 读 YAML → RulePack（Pydantic 校验）+ 计算内容 hash。
#       validate_dir(dir) 校验目录下所有规则包（Pydantic + hash）。
#       hash = sha256(canonical_json(policy_type/region/version/source/rule_text/display_text/rules))，
#       规则包 YAML 可声明 hash 自校验（loader 比对）。
#       CLI：python -m server.app.rule_engine.loader --validate config/rules。
# 边界：只加载校验，不持久化（持久化在 evidence_repo）；不改内核。

"""规则包 YAML 加载器（APC-T018）。

架构（ENGINEERING_DESIGN §13.2）：``config/rules/<domain>/<pack>-<version>.yaml``
→ Pydantic ``RulePack`` → 冻结策略 + hash 校验。``make rules-validate`` 调本模块 CLI。

- ``load_pack(path)``：读 YAML → RulePack（Pydantic 校验）+ 计算内容 hash。
- ``validate_dir(dir)``：校验目录下所有规则包（Pydantic + hash 自校验）。
- hash = sha256(canonical JSON of 规则包内容字段)，规则包 YAML 可声明 hash 自校验。
- CLI：``python -m server.app.rule_engine.loader --validate config/rules``。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from .domain.models import RulePack


def _compute_hash(pack_data: dict[str, Any]) -> str:
    """计算规则包内容 hash（sha256 of canonical JSON）。

    hash 覆盖策略内容字段（不含 hash 自身），用于校验完整性 + 版本一致性。
    canonical JSON：键排序、ensure_ascii=False，保证跨平台稳定。
    """
    content = {
        k: v
        for k, v in pack_data.items()
        if k != "hash"
    }
    canonical = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_pack(path: Path) -> RulePack:
    """加载单个规则包 YAML → RulePack（Pydantic 校验 + hash 计算/自校验）。

    若 YAML 声明 ``hash``，loader 比对计算 hash，不一致抛 ValueError（完整性校验）。
    未声明则填入计算 hash。
    """
    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"rule pack {path} must be a YAML mapping")
    computed = _compute_hash(raw)
    declared = raw.get("hash")
    if declared is not None and declared != computed:
        raise ValueError(
            f"rule pack {path} hash mismatch: declared={declared} computed={computed}"
        )
    raw["hash"] = computed
    return RulePack.model_validate(raw)


def validate_dir(dir_path: Path) -> list[RulePack]:
    """校验目录下所有 ``*.yaml`` 规则包（Pydantic + hash）。

    返回加载成功的 RulePack 列表；任一校验失败抛异常（CLI 退出非 0）。
    """
    packs: list[RulePack] = []
    yaml_files = sorted(dir_path.rglob("*.yaml"))
    for path in yaml_files:
        packs.append(load_pack(path))
    return packs


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：``--validate <dir>`` 校验规则包。"""
    args = argv if argv is not None else sys.argv[1:]
    if len(args) >= 2 and args[0] == "--validate":
        dir_path = Path(args[1])
        if not dir_path.is_dir():
            print(f"rules-validate: {dir_path} is not a directory", file=sys.stderr)
            return 2
        packs = validate_dir(dir_path)
        print(f"rules-validate: {len(packs)} rule pack(s) OK")
        for p in packs:
            print(f"  - {p.policy_type}/{p.region}@v{p.version} rules={len(p.rules)} hash={p.hash[:12]}")
        return 0
    print("usage: python -m server.app.rule_engine.loader --validate <dir>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["load_pack", "main", "validate_dir"]

# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
"""规则包 YAML 加载器单元测试（APC-T018）。

覆盖 load_pack（Pydantic 校验 + hash 计算/自校验）、validate_dir、CLI main。
用 tmp_path 写临时 YAML，不依赖 config/rules 真实文件。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from server.app.rule_engine.loader import _compute_hash, load_pack, main, validate_dir

VALID_YAML = """
policy_type: triage
region: CN
version: 1
effective_from: 2026-08-16T00:00:00+08:00
source: "test"
rule_text: "r"
display_text: "d"
rules:
  - rule_id: r1
    conditions:
      - op: lt
        field: baby_age_days
        value: 90
    action:
      verdict: warn
      outputs: {alert_level: yellow}
      reason_code: r1
      evidence_text: "e"
"""


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_load_pack_valid(tmp_path: Path):
    p = _write(tmp_path / "base-1.yaml", VALID_YAML)
    pack = load_pack(p)
    assert pack.policy_type == "triage"
    assert pack.region == "CN"
    assert pack.version == 1
    assert len(pack.rules) == 1
    assert pack.rules[0].rule_id == "r1"
    assert pack.hash is not None and len(pack.hash) == 64  # sha256 hex


def test_load_pack_fills_computed_hash_when_absent(tmp_path: Path):
    p = _write(tmp_path / "base-1.yaml", VALID_YAML)
    pack = load_pack(p)
    # 计算的 hash 与 loader 填入一致。
    import yaml

    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert pack.hash == _compute_hash(raw)


def test_load_pack_declared_hash_match(tmp_path: Path):
    # 先算 hash，再写回 YAML 声明，loader 自校验通过。
    import yaml

    raw = yaml.safe_load(VALID_YAML)
    h = _compute_hash(raw)
    raw["hash"] = h
    p = _write(tmp_path / "base-1.yaml", yaml.safe_dump(raw, allow_unicode=True))
    pack = load_pack(p)
    assert pack.hash == h


def test_load_pack_declared_hash_mismatch_raises(tmp_path: Path):
    import yaml

    raw = yaml.safe_load(VALID_YAML)
    raw["hash"] = "deadbeef" * 8  # 错误 hash。
    p = _write(tmp_path / "base-1.yaml", yaml.safe_dump(raw, allow_unicode=True))
    with pytest.raises(ValueError, match="hash mismatch"):
        load_pack(p)


def test_load_pack_non_mapping_raises(tmp_path: Path):
    p = _write(tmp_path / "bad.yaml", "- 1\n- 2\n")
    with pytest.raises(ValueError, match="must be a YAML mapping"):
        load_pack(p)


def test_load_pack_missing_required_field_raises(tmp_path: Path):
    bad = VALID_YAML.replace("version: 1\n", "")  # 缺 version。
    p = _write(tmp_path / "bad.yaml", bad)
    with pytest.raises(ValidationError):  # Pydantic 缺必填字段。
        load_pack(p)


def test_validate_dir_loads_all_yaml(tmp_path: Path):
    _write(tmp_path / "a-1.yaml", VALID_YAML)
    _write(tmp_path / "b-1.yaml", VALID_YAML.replace("policy_type: triage", 'policy_type: "x"'))
    packs = validate_dir(tmp_path)
    assert len(packs) == 2


def test_validate_dir_empty_dir_returns_empty(tmp_path: Path):
    assert validate_dir(tmp_path) == []


def test_main_validate_ok(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    _write(tmp_path / "base-1.yaml", VALID_YAML)
    rc = main(["--validate", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "1 rule pack(s) OK" in out


def test_main_validate_not_a_dir(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    f = _write(tmp_path / "f.yaml", VALID_YAML)
    rc = main(["--validate", str(f)])
    assert rc == 2
    assert "not a directory" in capsys.readouterr().err


def test_main_no_args_prints_usage(capsys: pytest.CaptureFixture[str]):
    rc = main([])
    assert rc == 2
    assert "usage" in capsys.readouterr().err

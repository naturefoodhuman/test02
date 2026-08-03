# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-03 23:20:00

"""launchd plist static validator for local deployment runbooks."""

from __future__ import annotations

import plistlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class LaunchdValidationResult:
    path: str
    label: str
    ok: bool
    errors: tuple[str, ...]


REQUIRED_KEYS = ("Label", "ProgramArguments")


def validate_launchd_plist(path: Path | str) -> LaunchdValidationResult:
    plist_path = Path(path)
    errors: list[str] = []
    try:
        data = plistlib.loads(plist_path.read_bytes())
    except Exception as exc:
        return LaunchdValidationResult(
            path=str(plist_path),
            label="",
            ok=False,
            errors=(f"invalid plist xml: {exc}",),
        )
    label = str(data.get("Label", ""))
    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"missing required key: {key}")
    args = data.get("ProgramArguments")
    if not isinstance(args, list) or not args or not all(isinstance(item, str) for item in args):
        errors.append("ProgramArguments must be a non-empty string array")
    for key in ("StandardOutPath", "StandardErrorPath"):
        _validate_log_path(data, key, errors)
    if data.get("RunAtLoad") is True and "WorkingDirectory" not in data:
        errors.append("RunAtLoad jobs must declare WorkingDirectory")
    return LaunchdValidationResult(
        path=str(plist_path),
        label=label,
        ok=not errors,
        errors=tuple(errors),
    )


def validate_launchd_directory(
    root: Path | str = "deploy/launchd",
) -> list[LaunchdValidationResult]:
    return [validate_launchd_plist(path) for path in sorted(Path(root).glob("*.plist"))]


def _validate_log_path(data: dict[str, Any], key: str, errors: list[str]) -> None:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        errors.append(f"{key} must be set")
        return
    if value.startswith("/tmp/"):
        errors.append(f"{key} must not write to /tmp; use runtime/logs")
    if not (value.startswith("runtime/logs/") or "/runtime/logs/" in value):
        errors.append(f"{key} must write under runtime/logs")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default="deploy/launchd")
    args = parser.parse_args()
    results = validate_launchd_directory(Path(args.root))
    for result in results:
        status = "ok" if result.ok else "fail"
        print(f"{status} {result.label} {result.path}")
        for error in result.errors:
            print(f"  - {error}")
    failed = [result for result in results if not result.ok]
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

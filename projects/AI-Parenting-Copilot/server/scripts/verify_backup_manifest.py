#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-03 23:35:00

"""Verify a backup manifest and print restore-drill next commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from server.app.backup.verification import BackupManifestVerifier


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", help="Path to backup manifest JSON")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--require-files", action="store_true")
    parser.add_argument(
        "--restore-database-url",
        default="postgresql://parenting:parenting@127.0.0.1:5432/parenting_restore",
    )
    args = parser.parse_args()

    result = BackupManifestVerifier(project_root=Path(args.project_root)).verify_manifest_file(
        args.manifest,
        require_files=args.require_files,
        restore_database_url=args.restore_database_url,
    )
    print(result.to_json())
    if not result.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

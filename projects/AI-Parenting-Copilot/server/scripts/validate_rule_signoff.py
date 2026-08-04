#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 22:58:00

"""Generate or validate rule review sign-off artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from server.app.rule_engine.review_signoff import (
    build_signoff_template,
    load_signoff_file,
    validate_rule_signoff,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--signoff")
    parser.add_argument("--template-domain")
    parser.add_argument("--scope", default="dev_shadow")
    args = parser.parse_args()

    if args.template_domain:
        template = build_signoff_template(
            args.template_domain,
            project_root=Path(args.project_root),
            scope=args.scope,
        )
        print(template.to_dict())
        return
    if not args.signoff:
        raise SystemExit("Provide --signoff or --template-domain")
    signoff = load_signoff_file(args.signoff)
    result = validate_rule_signoff(signoff, project_root=Path(args.project_root))
    print(result.to_json())
    if not result.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

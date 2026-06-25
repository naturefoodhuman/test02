# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-25 00:00:00
"""
Documentation Governance Continuous Check Generator.

This script operationalizes DOCUMENT_AUDIT_REPORT.md as a repeatable check.
It is intentionally lightweight: no external dependencies, safe to run locally,
and suitable for Makefile / pre-commit / launchd / CI style automation.

Usage:
  python3 scripts/governance_check.py
  python3 scripts/governance_check.py --output docs/GOVERNANCE_CHECK_YYYY-MM-DD.md
  python3 scripts/governance_check.py --strict

Outputs:
- dated docs/GOVERNANCE_CHECK_YYYY-MM-DD.md unless --output is provided
- docs/GOVERNANCE_CHECK_LATEST.md
- stdout summary
- non-zero exit in --strict mode when blocking issues are found
"""
from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
ADR_DIR = DOCS_DIR / "adr"
PLATFORM_DIR = ROOT / "_factory" / "patterns" / "peer-review" / "src" / "peer_review"

LLM_HEADER_RE = re.compile(r"创建/修改该文件的LLM大模型：\s*[^\n]+")
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)(?:#[^)]+)?\)")

CORE_SSOT_FILES = [
    "HANDOFF.md",
    "README.md",
    "docs/PROJECT_STATE.md",
    "TASK_BACKLOG.md",
    "NETWORK_ARCHITECTURE_FINAL.md",
    "NETWORK_ENGINEERING_DESIGN.md",
    "docs/DEV_LOG.md",
    "docs/CHANGELOG.md",
    "docs/adr/README.md",
]

EXCLUDE_MARKERS = [
    ".venv",
    "__pycache__",
    "build",
    "dist",
    ".tox",
    "node_modules",
    ".git",
    ".arena",
    "diagnostics/snapshots",
]


def beijing_time() -> str:
    return (datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")


def _read_head(path: Path, limit: int = 500) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except Exception:
        return ""


def has_llm_header_py(path: Path) -> bool:
    return bool(LLM_HEADER_RE.search(_read_head(path, 300)))


def has_llm_header_md(path: Path) -> bool:
    head = _read_head(path, 500)
    return "<!--" in head and bool(LLM_HEADER_RE.search(head))


def _is_relevant(path: Path) -> bool:
    s = str(path.relative_to(ROOT)) if path.is_absolute() else str(path)
    return not any(marker in s for marker in EXCLUDE_MARKERS)


def count_active_zip_refs_in_core_docs() -> int:
    count = 0
    for name in CORE_SSOT_FILES + ["DOCUMENT_AUDIT_REPORT.md", "DOCUMENT_CHANGE_REPORT.md"]:
        path = ROOT / name
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        if "已于 2026-06-16 正式废弃" in content or "Phase 1 已彻底清理" in content:
            continue
        if re.search(r"\.zip|_patches|ZIP 补丁|zip 补丁", content, re.IGNORECASE):
            count += 1
    return count


def count_old_agno_mentions() -> dict[str, int]:
    bad_imports = [
        "from peer_review.orchestrator",
        "import peer_review.orchestrator",
        "from peer_review.knowledge_loader",
        "from peer_review.agent_factory",
    ]
    results: dict[str, int] = {k: 0 for k in bad_imports}
    if not PLATFORM_DIR.exists():
        return results
    for py in PLATFORM_DIR.rglob("*.py"):
        if py.name in {"orchestrator.py", "knowledge_loader.py", "agent_factory.py"}:
            continue
        txt = py.read_text(encoding="utf-8", errors="ignore")
        for bad in bad_imports:
            if bad in txt:
                results[bad] += 1
    return results


def scan_adr_coverage() -> dict[str, Any]:
    adrs = sorted(ADR_DIR.glob("ADR-*.md")) if ADR_DIR.exists() else []
    return {
        "total": len(adrs),
        "with_headers": sum(1 for a in adrs if has_llm_header_md(a)),
        "list": [a.name for a in adrs],
    }


def scan_r5_compliance() -> dict[str, Any]:
    py_relevant = [f for f in ROOT.rglob("*.py") if _is_relevant(f)]
    md_relevant = [f for f in ROOT.rglob("*.md") if _is_relevant(f)]
    return {
        "python": {"total": len(py_relevant), "ok": sum(1 for f in py_relevant if has_llm_header_py(f))},
        "markdown": {"total": len(md_relevant), "ok": sum(1 for f in md_relevant if has_llm_header_md(f))},
    }


def scan_cross_refs_to_adr() -> int:
    if not PLATFORM_DIR.exists():
        return 0
    count = 0
    for py in PLATFORM_DIR.rglob("*.py"):
        if "docs/adr/ADR-" in py.read_text(encoding="utf-8", errors="ignore"):
            count += 1
    return count


def scan_core_ssot_existence() -> list[str]:
    return [name for name in CORE_SSOT_FILES if not (ROOT / name).exists()]


def scan_missing_core_doc_links() -> list[str]:
    """Find missing .md links in current core docs, ignoring historical changelog/devlog."""
    missing: set[str] = set()
    scan_files = [
        ROOT / "HANDOFF.md",
        ROOT / "README.md",
        ROOT / "docs" / "PROJECT_STATE.md",
        ROOT / "docs" / "工厂使用手册.md",
        ROOT / "docs" / "全功能最小示例项目.md",
        ROOT / "docs" / "工厂能力覆盖检查.md",
    ]
    for source in scan_files:
        if not source.exists():
            continue
        txt = source.read_text(encoding="utf-8", errors="ignore")
        for match in MD_LINK_RE.finditer(txt):
            raw = match.group(1)
            if not raw or raw.startswith(("http://", "https://")):
                continue
            target = (source.parent / raw).resolve() if not raw.startswith("/") else Path(raw)
            if not target.exists():
                # Also try repo-root relative paths for docs that mention root files.
                root_target = (ROOT / raw).resolve()
                if not root_target.exists():
                    missing.add(f"{source.relative_to(ROOT)} -> {raw}")
    return sorted(missing)


def classify_blockers() -> dict[str, Any]:
    adr = scan_adr_coverage()
    r5 = scan_r5_compliance()
    missing_ssot = scan_core_ssot_existence()
    missing_links = scan_missing_core_doc_links()
    zip_count = count_active_zip_refs_in_core_docs()
    agno_total = sum(count_old_agno_mentions().values())
    blockers = []
    warnings = []
    if missing_ssot:
        blockers.append(f"Missing SSOT docs: {missing_ssot}")
    if adr["total"] < 7:
        blockers.append("Factory ADR count below expected baseline 7")
    if zip_count > 0:
        blockers.append(f"Active ZIP/_patches refs in core docs: {zip_count}")
    if agno_total > 0:
        warnings.append(f"Old Agno imports remain: {agno_total}")
    if missing_links:
        warnings.append(f"Missing links in current core docs: {len(missing_links)}")
    for kind in ["python", "markdown"]:
        total = r5[kind]["total"]
        ok = r5[kind]["ok"]
        if total and ok / total < 0.75:
            warnings.append(f"R5 {kind} compliance below 75%: {ok}/{total}")
    return {"blockers": blockers, "warnings": warnings, "missing_links": missing_links}


def generate_report() -> str:
    ts = beijing_time()
    adr = scan_adr_coverage()
    r5 = scan_r5_compliance()
    zip_count = count_active_zip_refs_in_core_docs()
    agno = count_old_agno_mentions()
    cross_ref_count = scan_cross_refs_to_adr()
    missing_ssot = scan_core_ssot_existence()
    quality = classify_blockers()

    lines: list[str] = []
    lines.append(f"<!--\n创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer\n创建时间（北京时间）：{ts}\n-->")
    lines.append("")
    lines.append(f"# Governance Health Check — {ts.split()[0]} (Automated)")
    lines.append("")
    lines.append(f"**Generated by**: `scripts/governance_check.py` at {ts} (Beijing)")
    lines.append("**Framework**: Documentation Governance & Audit + SSOT + ADR + R5 + Continuous Governance")
    lines.append("")
    lines.append("## 1. Blocking Status")
    if quality["blockers"]:
        lines.append("- Status: BLOCKED")
        for item in quality["blockers"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- Status: PASS（无阻断级治理问题）")
    if quality["warnings"]:
        lines.append("- Warnings:")
        for item in quality["warnings"]:
            lines.append(f"  - {item}")
    lines.append("")
    lines.append("## 2. ADR Coverage")
    lines.append(f"- Factory ADRs: **{adr['total']}**")
    lines.append(f"- With LLM headers: **{adr['with_headers']}/{adr['total']}**")
    lines.append(f"- ADR list: {', '.join(adr['list']) if adr['list'] else '<none>'}")
    lines.append("")
    lines.append("## 3. R5 LLM File Header Compliance")
    lines.append(f"- Python: **{r5['python']['ok']}/{r5['python']['total']}**")
    lines.append(f"- Markdown: **{r5['markdown']['ok']}/{r5['markdown']['total']}**")
    lines.append("- Header rule accepts any non-empty model identity after `创建/修改该文件的LLM大模型：`.")
    lines.append("")
    lines.append("## 4. Stale / Legacy Signals")
    lines.append(f"- Active ZIP/_patches refs in core docs: **{zip_count}**")
    lines.append(f"- Old Agno bad imports in new platform code: **{sum(agno.values())}**")
    lines.append(f"- Platform files referencing ADRs: **{cross_ref_count}**")
    lines.append("")
    lines.append("## 5. SSOT Existence")
    if missing_ssot:
        lines.append(f"- Missing: {', '.join(missing_ssot)}")
    else:
        lines.append("- All required SSOT docs exist.")
    lines.append("")
    lines.append("## 6. Missing Links in Current Core Docs")
    if quality["missing_links"]:
        for item in quality["missing_links"][:50]:
            lines.append(f"- {item}")
    else:
        lines.append("- None detected in current onboarding/core docs.")
    lines.append("")
    lines.append("## 7. Recommended Automation Cadence")
    lines.append("- Every development turn: run `make docs-check` before commit.")
    lines.append("- Every significant architecture/workflow change: add ADR, then run `make governance-check` and commit dated report.")
    lines.append("- Weekly or every 5 turns: run full documentation audit and review `DOCUMENT_AUDIT_REPORT.md` deltas.")
    lines.append("- Before handoff: verify `HANDOFF.md`, `PROJECT_STATE.md`, `TASK_BACKLOG.md`, `DEV_LOG.md`, `CHANGELOG.md` are current.")
    lines.append("")
    lines.append("---")
    lines.append("*Auto-generated. Do not edit manually; re-run the script after changes.*")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=None, help="Explicit output path (otherwise auto-dated)")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on blocking governance issues")
    args = parser.parse_args()

    report = generate_report()
    today = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")
    dated_path = DOCS_DIR / f"GOVERNANCE_CHECK_{today}.md"
    latest_path = DOCS_DIR / "GOVERNANCE_CHECK_LATEST.md"
    target = Path(args.output) if args.output else dated_path

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report, encoding="utf-8")
    latest_path.write_text(report, encoding="utf-8")

    quality = classify_blockers()
    print(f"✅ Wrote governance check: {target}")
    print(f"✅ Updated LATEST: {latest_path}")
    print("\n=== Governance Check Summary ===")
    print(f"Blockers: {len(quality['blockers'])}")
    print(f"Warnings: {len(quality['warnings'])}")
    r5 = scan_r5_compliance()
    print(f"R5 Python: {r5['python']['ok']}/{r5['python']['total']}")
    print(f"R5 Markdown: {r5['markdown']['ok']}/{r5['markdown']['total']}")
    print(f"Missing links: {len(quality['missing_links'])}")
    if args.strict and quality["blockers"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

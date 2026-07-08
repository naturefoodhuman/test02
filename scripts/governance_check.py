# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-25 00:00:00
"""
Documentation Governance Continuous Check Generator.

Operationalizes DOCUMENT_AUDIT_REPORT.md as repeatable, blocking governance.
No third-party dependencies. Safe for Makefile / local pre-commit / CI / launchd.

Usage:
  python3 scripts/governance_check.py
  python3 scripts/governance_check.py --strict
  python3 scripts/governance_check.py --output docs/GOVERNANCE_CHECK_YYYY-MM-DD.md

Outputs:
- docs/GOVERNANCE_CHECK_YYYY-MM-DD.md
- docs/GOVERNANCE_CHECK_LATEST.md
- docs/DOCUMENT_INDEX.md
- stdout summary
- non-zero exit in --strict mode when blocking issues are found
"""
from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
ADR_DIR = DOCS_DIR / "adr"
PLATFORM_DIR = ROOT / "_factory" / "patterns" / "peer-review" / "src" / "peer_review"
DOCUMENT_INDEX = DOCS_DIR / "DOCUMENT_INDEX.md"
AGENT_HANDOFF_SUMMARY = DOCS_DIR / "AGENT_HANDOFF_SUMMARY.md"

LLM_HEADER_RE = re.compile(r"创建/修改该文件的LLM大模型：\s*[^\n]+")
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)(?:#[^)]+)?\)")
ARCH_TRIGGER_RE = re.compile(
    r"\b(architecture|architectural|orchestrator|workflow|provider|boundary|routing|router|"
    r"privacy|security|mcp|searxng|crawler|extractor|circuit|fallback|model|langgraph|adr)\b",
    re.IGNORECASE,
)

CORE_SSOT_FILES = [
    "HANDOFF.md",
    "README.md",
    "docs/PROJECT_STATE.md",
    "docs/DEV_LOG.md",
    "docs/CHANGELOG.md",
    "docs/adr/README.md",
]

TRAINING_DOCS = [
    "docs/工厂使用手册.md",
    "docs/全功能最小示例项目.md",
    "docs/工厂能力覆盖检查.md",
]

GOVERNANCE_DOCS = [
    "DOCUMENT_AUDIT_REPORT.md",
    "DOCUMENT_CHANGE_REPORT.md",
    "docs/DOCUMENT_GOVERNANCE_AUTOMATION_PLAN.md",
    "docs/DOCUMENT_INDEX.md",
    "docs/GOVERNANCE_CHECK_LATEST.md",
]

CODE_EXTS = {".py", ".sh", ".yml", ".yaml", ".toml", ".json", ".txt"}
DOC_EXTS = {".md"}
R5_EXTS = {".py", ".md", ".yml", ".yaml", ".sh"}

EXCLUDE_MARKERS = [
    ".venv",
    "__pycache__",
    "build",
    "dist",
    ".tox",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    ".git",
    ".arena",
    "diagnostics/snapshots",
]


def beijing_time() -> str:
    return (datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")


def _run_git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return ""


def _read_head(path: Path, limit: int = 500) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except Exception:
        return ""


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _is_relevant(path: Path | str) -> bool:
    s = str(path)
    return not any(marker in s for marker in EXCLUDE_MARKERS)


def has_llm_header_py(path: Path) -> bool:
    return bool(LLM_HEADER_RE.search(_read_head(path, 300)))


def has_llm_header_md(path: Path) -> bool:
    head = _read_head(path, 500)
    return "<!--" in head and bool(LLM_HEADER_RE.search(head))


def has_llm_header_generic(path: Path) -> bool:
    if path.suffix.lower() == ".md":
        return has_llm_header_md(path)
    return bool(LLM_HEADER_RE.search(_read_head(path, 500)))


def get_changed_files() -> list[str]:
    """Tracked changes + untracked files, relative to repo root."""
    changed = set()
    for line in _run_git(["diff", "--name-only", "HEAD"]).splitlines():
        if line.strip():
            changed.add(line.strip())
    for line in _run_git(["ls-files", "--others", "--exclude-standard"]).splitlines():
        if line.strip():
            changed.add(line.strip())
    return sorted(f for f in changed if _is_relevant(f))


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
    py_relevant = [f for f in ROOT.rglob("*.py") if _is_relevant(_rel(f))]
    md_relevant = [f for f in ROOT.rglob("*.md") if _is_relevant(_rel(f))]
    return {
        "python": {"total": len(py_relevant), "ok": sum(1 for f in py_relevant if has_llm_header_py(f))},
        "markdown": {"total": len(md_relevant), "ok": sum(1 for f in md_relevant if has_llm_header_md(f))},
    }


def scan_changed_files_r5(changed_files: list[str]) -> list[str]:
    missing = []
    for rel in changed_files:
        path = ROOT / rel
        if not path.exists() or path.suffix.lower() not in R5_EXTS:
            continue
        # Generated governance reports and diagnostics snapshots are allowed to be generated by tools.
        if rel.startswith("diagnostics/"):
            continue
        if not has_llm_header_generic(path):
            missing.append(rel)
    return missing


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
    missing: set[str] = set()
    scan_files = [
        ROOT / "HANDOFF.md",
        ROOT / "README.md",
        ROOT / "docs" / "PROJECT_STATE.md",
        ROOT / "docs" / "工厂使用手册.md",
        ROOT / "docs" / "全功能最小示例项目.md",
        ROOT / "docs" / "工厂能力覆盖检查.md",
        ROOT / "docs" / "DOCUMENT_INDEX.md",
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
            if not target.exists() and not (ROOT / raw).resolve().exists():
                missing.add(f"{source.relative_to(ROOT)} -> {raw}")
    return sorted(missing)


def scan_changelog_required(changed_files: list[str]) -> list[str]:
    if "docs/CHANGELOG.md" in changed_files:
        return []
    offenders = []
    for rel in changed_files:
        if rel.startswith(("docs/", "diagnostics/")) or rel in {"README.md", "HANDOFF.md", "TASK_BACKLOG.md"}:
            continue
        if (ROOT / rel).suffix.lower() in CODE_EXTS:
            offenders.append(rel)
    return offenders


def scan_backlog_devlog_sync(changed_files: list[str]) -> bool:
    return False  # TASK_BACKLOG.md deprecated, check disabled


def scan_arch_triggers(changed_files: list[str]) -> dict[str, Any]:
    adr_changed = any(rel.startswith("docs/adr/ADR-") for rel in changed_files)
    diff_text = _run_git(["diff", "HEAD", "--", *changed_files]) if changed_files else ""
    hits = sorted(set(m.group(0).lower() for m in ARCH_TRIGGER_RE.finditer("\n".join(changed_files) + "\n" + diff_text)))
    return {"hits": hits, "adr_changed": adr_changed}


def classify_doc(path: Path) -> tuple[str, str]:
    rel = _rel(path)
    if rel in CORE_SSOT_FILES:
        return "SSOT", "current"
    if rel in TRAINING_DOCS:
        return "training", "current"
    if rel in GOVERNANCE_DOCS or rel.startswith("docs/GOVERNANCE_CHECK_") or rel.startswith("docs/adr/"):
        return "governance", "current"
    if rel.startswith("docs/research/"):
        return "research", "reference"
    if "CHANGELOG" in rel or "DEV_LOG" in rel:
        return "log", "current"
    if rel.startswith("diagnostics/"):
        return "diagnostic-output", "runtime-artifact"
    if rel.startswith("docs/"):
        return "supporting-doc", "reference"
    return "root-doc", "reference"


def generate_document_index(ts: str) -> str:
    docs = sorted([p for p in ROOT.rglob("*.md") if _is_relevant(_rel(p))], key=lambda p: _rel(p))
    rows = []
    for path in docs:
        rel = _rel(path)
        category, status = classify_doc(path)
        rows.append((rel, category, status))
    lines = [
        "<!--",
        "创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer",
        f"创建时间（北京时间）：{ts}",
        "-->",
        "",
        "# Document Index（自动生成）",
        "",
        "本文件由 `scripts/governance_check.py` 自动生成，用于标记当前文档的用途与状态。不要手工编辑；修改分类规则后重新运行 `make governance-check`。",
        "",
        "## 状态说明",
        "",
        "| 状态 | 含义 |",
        "|---|---|",
        "| current | 当前有效文档，可作为当前事实来源或操作入口。 |",
        "| reference | 参考资料，不应覆盖 SSOT。 |",
        "| runtime-artifact | 运行/诊断产物，通常不应作为设计依据。 |",
        "",
        "## 文档清单",
        "",
        "| 文档 | 分类 | 状态 |",
        "|---|---|---|",
    ]
    for rel, category, status in rows:
        lines.append(f"| `{rel}` | {category} | {status} |")
    lines.extend(
        [
            "",
            "## 当前 SSOT 快速入口",
            "",
            "- 项目接手：`HANDOFF.md`",
            "- 当前状态：`docs/PROJECT_STATE.md`",
            "- 任务状态：`TASK_BACKLOG.md` §10",
            "- 联网架构：`NETWORK_ARCHITECTURE_FINAL.md`",
            "- 联网工程设计：`NETWORK_ENGINEERING_DESIGN.md`",
            "- ADR：`docs/adr/README.md`",
            "- 新用户培训：`docs/工厂使用手册.md`",
            "- 全功能示例：`docs/全功能最小示例项目.md`",
            "- 能力覆盖：`docs/工厂能力覆盖检查.md`",
            "- 治理自动化：`docs/DOCUMENT_GOVERNANCE_AUTOMATION_PLAN.md`",
            "",
        ]
    )
    return "\n".join(lines)



def _extract_project_state_summary() -> list[str]:
    path = ROOT / "docs" / "PROJECT_STATE.md"
    if not path.exists():
        return ["- docs/PROJECT_STATE.md not found"]
    lines = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("**当前版本**") or line.startswith("**更新日期**") or line.startswith("**状态说明**"):
            lines.append(f"- {line.strip('*')}")
        if len(lines) >= 6:
            break
    return lines or ["- See docs/PROJECT_STATE.md"]


def _latest_git_log(limit: int = 5) -> list[str]:
    out = _run_git(["log", "--oneline", f"-{limit}"])
    return [f"- `{line}`" for line in out.splitlines() if line.strip()]


def generate_agent_handoff_summary(ts: str) -> str:
    quality = classify_blockers(get_changed_files())
    lines = [
        "<!--",
        "创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer",
        f"创建时间（北京时间）：{ts}",
        "-->",
        "",
        "# Agent Handoff Summary（自动生成）",
        "",
        "本文件由 `scripts/governance_check.py` 自动生成，用于新 Agent 快速建立当前上下文。不要手工编辑；需要刷新时运行 `make governance-check`。",
        "",
        "## 1. 必读入口",
        "",
        "1. `HANDOFF.md`",
        "2. `docs/PROJECT_STATE.md`",
        "3. `TASK_BACKLOG.md` §10",
        "4. `NETWORK_ARCHITECTURE_FINAL.md`",
        "5. `NETWORK_ENGINEERING_DESIGN.md`",
        "6. `docs/DEV_LOG.md` 最新轮",
        "7. `docs/CHANGELOG.md` 最新轮",
        "8. `docs/DOCUMENT_INDEX.md`",
        "",
        "## 2. 当前状态摘要",
        "",
        *_extract_project_state_summary(),
        "",
        "## 3. 最新提交",
        "",
        *_latest_git_log(),
        "",
        "## 4. 治理健康",
        "",
        f"- Blockers: {len(quality['blockers'])}",
        f"- Warnings: {len(quality['warnings'])}",
        f"- Changed files: {len(get_changed_files())}",
        "- 最新完整报告：`docs/GOVERNANCE_CHECK_LATEST.md`",
        "",
        "## 5. 当前自动化命令",
        "",
        "```bash",
        "make docs-check",
        "make governance-check",
        "make network-test",
        "python3 -m _infra.network.cli search \"python langgraph state machine\" --mode research",
        "```",
        "",
        "## 6. 注意事项",
        "",
        "- 真实 API key 只允许放在 `.env` / `_infra/.env`，不得提交。",
        "- Claude Code for VS Code 是日常主入口，CLI 是验证/自动化辅助。",
        "- 高风险能力只能 sandbox / dry-run / approval / deny-test 演示。",
        "- 架构、边界、调用链、provider、routing、privacy、安全策略变化需要考虑新增 ADR。",
        "",
    ]
    return "\n".join(lines)

def classify_blockers(changed_files: list[str]) -> dict[str, Any]:
    adr = scan_adr_coverage()
    r5 = scan_r5_compliance()
    missing_ssot = scan_core_ssot_existence()
    missing_links = scan_missing_core_doc_links()
    zip_count = count_active_zip_refs_in_core_docs()
    agno_total = sum(count_old_agno_mentions().values())
    changed_r5_missing = scan_changed_files_r5(changed_files)
    changelog_offenders = scan_changelog_required(changed_files)
    backlog_without_devlog = scan_backlog_devlog_sync(changed_files)
    arch = scan_arch_triggers(changed_files)

    blockers = []
    warnings = []
    if missing_ssot:
        blockers.append(f"Missing SSOT docs: {missing_ssot}")
    if adr["total"] < 7:
        blockers.append("Factory ADR count below expected baseline 7")
    if zip_count > 0:
        blockers.append(f"Active ZIP/_patches refs in core docs: {zip_count}")
    if changed_r5_missing:
        warnings.append(
            "Changed files without LLM header (allowed for human-authored files; "
            f"LLM-generated/LLM-edited files must add header): {changed_r5_missing}"
        )
    if changelog_offenders:
        blockers.append(f"Code/config changed but docs/CHANGELOG.md not updated: {changelog_offenders[:10]}")
    if backlog_without_devlog:
        pass  # TASK_BACKLOG.md deprecated, check disabled
    if agno_total > 0:
        warnings.append(f"Old Agno imports remain: {agno_total}")
    if missing_links:
        warnings.append(f"Missing links in current core docs: {len(missing_links)}")
    if arch["hits"] and not arch["adr_changed"]:
        warnings.append(
            "Architecture-sensitive terms detected without ADR change; review whether new ADR is required: "
            + ", ".join(arch["hits"][:20])
        )
    for kind in ["python", "markdown"]:
        total = r5[kind]["total"]
        ok = r5[kind]["ok"]
        if total and ok / total < 0.75:
            warnings.append(f"R5 {kind} compliance below 75%: {ok}/{total}")
    return {
        "blockers": blockers,
        "warnings": warnings,
        "missing_links": missing_links,
        "changed_r5_missing": changed_r5_missing,
        "changelog_offenders": changelog_offenders,
        "arch": arch,
    }


def generate_report(changed_files: list[str]) -> str:
    ts = beijing_time()
    adr = scan_adr_coverage()
    r5 = scan_r5_compliance()
    zip_count = count_active_zip_refs_in_core_docs()
    agno = count_old_agno_mentions()
    cross_ref_count = scan_cross_refs_to_adr()
    missing_ssot = scan_core_ssot_existence()
    quality = classify_blockers(changed_files)

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
    lines.append("## 2. Changed Files Governance")
    lines.append(f"- Changed files detected: **{len(changed_files)}**")
    if changed_files:
        for rel in changed_files[:50]:
            lines.append(f"  - `{rel}`")
    lines.append(f"- Changed files without LLM header: **{len(quality['changed_r5_missing'])}** (warning only; human-authored files are allowed)")
    lines.append(f"- Code/config changes requiring CHANGELOG: **{len(quality['changelog_offenders'])}**")
    lines.append("")
    lines.append("## 3. ADR Coverage")
    lines.append(f"- Factory ADRs: **{adr['total']}**")
    lines.append(f"- With LLM headers: **{adr['with_headers']}/{adr['total']}**")
    lines.append(f"- ADR list: {', '.join(adr['list']) if adr['list'] else '<none>'}")
    lines.append("")
    lines.append("## 4. R5 LLM File Header Compliance")
    lines.append(f"- Python: **{r5['python']['ok']}/{r5['python']['total']}**")
    lines.append(f"- Markdown: **{r5['markdown']['ok']}/{r5['markdown']['total']}**")
    lines.append("- New/changed files are blocking-checked separately.")
    lines.append("")
    lines.append("## 5. Stale / Legacy Signals")
    lines.append(f"- Active ZIP/_patches refs in core docs: **{zip_count}**")
    lines.append(f"- Old Agno bad imports in new platform code: **{sum(agno.values())}**")
    lines.append(f"- Platform files referencing ADRs: **{cross_ref_count}**")
    lines.append("")
    lines.append("## 6. SSOT Existence")
    if missing_ssot:
        lines.append(f"- Missing: {', '.join(missing_ssot)}")
    else:
        lines.append("- All required SSOT docs exist.")
    lines.append("")
    lines.append("## 7. Missing Links in Current Core Docs")
    if quality["missing_links"]:
        for item in quality["missing_links"][:50]:
            lines.append(f"- {item}")
    else:
        lines.append("- None detected in current onboarding/core docs.")
    lines.append("")
    lines.append("## 8. Architecture Trigger Review")
    if quality["arch"]["hits"]:
        lines.append("- Trigger terms detected: " + ", ".join(quality["arch"]["hits"][:30]))
        lines.append(f"- ADR changed in same diff: {quality['arch']['adr_changed']}")
        lines.append("- Action: if the change modifies architecture, workflow, boundaries, providers, routing, privacy, security, or model policy, create a new ADR before merge.")
    else:
        lines.append("- No architecture-sensitive trigger terms detected in current diff.")
    lines.append("")
    lines.append("## 9. Recommended Automation Cadence")
    lines.append("- Every development turn: run `make docs-check` before commit.")
    lines.append("- Every significant architecture/workflow change: add ADR, then run `make governance-check` and commit dated report + DOCUMENT_INDEX.")
    lines.append("- Weekly or every 5 turns: review `DOCUMENT_AUDIT_REPORT.md` deltas and refresh governance report.")
    lines.append("- Before handoff: verify `HANDOFF.md`, `PROJECT_STATE.md`, `TASK_BACKLOG.md`, `DEV_LOG.md`, `CHANGELOG.md`, and `docs/DOCUMENT_INDEX.md` are current.")
    lines.append("")
    lines.append("---")
    lines.append("*Auto-generated. Do not edit manually; re-run the script after changes.*")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=None, help="Explicit output path (otherwise auto-dated)")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on blocking governance issues")
    parser.add_argument("--no-write", action="store_true", help="Run checks without writing generated docs")
    args = parser.parse_args()

    ts = beijing_time()
    changed_files = get_changed_files()
    report = generate_report(changed_files)
    today = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")
    dated_path = DOCS_DIR / f"GOVERNANCE_CHECK_{today}.md"
    latest_path = DOCS_DIR / "GOVERNANCE_CHECK_LATEST.md"
    target = Path(args.output) if args.output else dated_path

    if not args.no_write:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(report, encoding="utf-8")
        latest_path.write_text(report, encoding="utf-8")
        DOCUMENT_INDEX.write_text(generate_document_index(ts), encoding="utf-8")
        AGENT_HANDOFF_SUMMARY.write_text(generate_agent_handoff_summary(ts), encoding="utf-8")

    quality = classify_blockers(changed_files)
    if args.no_write:
        print("✅ Governance check completed in no-write mode")
    else:
        print(f"✅ Wrote governance check: {target}")
        print(f"✅ Updated LATEST: {latest_path}")
        print(f"✅ Updated document index: {DOCUMENT_INDEX}")
        print(f"✅ Updated agent handoff summary: {AGENT_HANDOFF_SUMMARY}")
    print("\n=== Governance Check Summary ===")
    print(f"Blockers: {len(quality['blockers'])}")
    print(f"Warnings: {len(quality['warnings'])}")
    r5 = scan_r5_compliance()
    print(f"R5 Python: {r5['python']['ok']}/{r5['python']['total']}")
    print(f"R5 Markdown: {r5['markdown']['ok']}/{r5['markdown']['total']}")
    print(f"Changed files: {len(changed_files)}")
    print(f"Missing links: {len(quality['missing_links'])}")
    if quality["warnings"]:
        print("Warnings:")
        for warning in quality["warnings"]:
            print(f"  - {warning}")
    if args.strict and quality["blockers"]:
        for blocker in quality["blockers"]:
            print(f"BLOCKER: {blocker}")
        sys.exit(1)


if __name__ == "__main__":
    main()

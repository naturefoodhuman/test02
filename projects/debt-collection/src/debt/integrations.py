# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-12 01:30:00 CST
"""接工厂通用能力：ingestion(资料整理) + acquisition(合规取数)。

设计：通过把工厂 Pattern 的 src 加入 sys.path 来复用（不重造轮子）。
工厂能力不可用时优雅降级（返回提示），保证 debt-collection 独立可跑。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# 工厂根：本项目在 projects/debt-collection/，回溯到工厂根 _factory/
_FACTORY = Path(__file__).resolve().parents[4] / "_factory"
_INGEST_SRC = _FACTORY / "patterns" / "ingestion-pipeline" / "src"
_ACQ_SRC = _FACTORY / "patterns" / "data-acquisition" / "src"
_TELEMETRY_SRC = _FACTORY / "patterns" / "llm-telemetry" / "src"

# 启动即把工厂遥测能力(R4)加入 path，供 strategy/llm_client 复用
if _TELEMETRY_SRC.exists():
    _tp = str(_TELEMETRY_SRC)
    if _tp not in sys.path:
        sys.path.insert(0, _tp)


def _ensure_path(p: Path) -> bool:
    if p.exists():
        sp = str(p)
        if sp not in sys.path:
            sys.path.insert(0, sp)
        return True
    return False


def ingest_materials(input_path: str, out_dir: str) -> dict[str, Any]:
    """调工厂 ingestion 把资料(合同/借据/录音)转结构化。

    Returns: {ok, docs:[...], error?}
    """
    if not _ensure_path(_INGEST_SRC):
        return {"ok": False, "error": f"未找到工厂 ingestion 能力：{_INGEST_SRC}"}
    try:
        from ingestion.pipeline import ingest_dir, ingest_file, save_doc  # type: ignore

        p = Path(input_path)
        docs = [ingest_file(p)] if p.is_file() else ingest_dir(p)
        saved = []
        for d in docs:
            md, js = save_doc(d, out_dir)
            saved.append({"source": d.source_path, "type": d.source_type.value,
                          "processor": d.meta.get("processor"), "md": str(md), "json": str(js),
                          "warnings": d.warnings})
        return {"ok": True, "docs": saved}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"ingestion 调用失败: {e}"}


def build_acquisition_plan(name: str, subject_type: str = "person",
                           region: str = "", out_dir: str = "runtime/acquisition") -> dict[str, Any]:
    """调工厂 acquisition 为债务人生成官方渠道待查清单。

    Returns: {ok, tasks:[...], checklist_md, error?}
    """
    if not _ensure_path(_ACQ_SRC):
        return {"ok": False, "error": f"未找到工厂 acquisition 能力：{_ACQ_SRC}"}
    try:
        from acquisition.models import Subject, SubjectType  # type: ignore
        from acquisition.planner import build_query_plan, save_plan  # type: ignore

        sub = Subject(name=name, region=region,
                      subject_type=SubjectType.COMPANY if subject_type == "company" else SubjectType.PERSON)
        plan = build_query_plan(sub)
        md, js = save_plan(plan, out_dir)
        return {"ok": True,
                "tasks": [{"source": t.source_name, "for": t.query_for,
                           "needs_captcha": t.needs_captcha, "needs_login": t.needs_login} for t in plan.tasks],
                "checklist_md": str(md)}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"acquisition 调用失败: {e}"}

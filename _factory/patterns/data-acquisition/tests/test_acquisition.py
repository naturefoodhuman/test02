# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-11 23:10:00 CST
"""L1 取数层测试（沙箱可跑通）。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acquisition.models import QueryResult, Subject, SubjectType  # noqa: E402
from acquisition.planner import archive_results, build_query_plan, save_plan  # noqa: E402
from acquisition.sources_registry import RiskLevel, get_source, list_sources  # noqa: E402


def test_registry_has_core_sources() -> None:
    for k in ("zxgk", "wenshu", "gsxt", "flk"):
        assert get_source(k) is not None


def test_list_sources_risk_filter() -> None:
    low = list_sources(max_risk=RiskLevel.LOW)
    keys = {s.key for s in low}
    assert "wenshu" not in keys      # wenshu 是 medium，应被过滤
    assert "zxgk" in keys and "flk" in keys


def test_plan_for_person() -> None:
    sub = Subject(name="张三", subject_type=SubjectType.PERSON, region="浙江杭州")
    plan = build_query_plan(sub)
    keys = [t.source_key for t in plan.tasks]
    assert "zxgk" in keys           # 自然人必查执行信息
    assert "wenshu" in keys         # 必查裁判文书
    assert "flk" in keys            # 法条核对


def test_plan_for_company_includes_gsxt() -> None:
    sub = Subject(name="某某公司", subject_type=SubjectType.COMPANY)
    plan = build_query_plan(sub)
    assert "gsxt" in [t.source_key for t in plan.tasks]


def test_plan_max_risk_low_excludes_wenshu() -> None:
    sub = Subject(name="张三")
    plan = build_query_plan(sub, max_risk=RiskLevel.LOW)
    assert "wenshu" not in [t.source_key for t in plan.tasks]


def test_checklist_md_renders() -> None:
    sub = Subject(name="张三", region="杭州")
    plan = build_query_plan(sub)
    md = plan.to_checklist_md()
    assert "取数待查清单：张三" in md
    assert "中国执行信息公开网" in md
    assert "账号安全" in md          # 合规提示在

def test_save_plan_and_archive(tmp_path) -> None:
    sub = Subject(name="张三")
    plan = build_query_plan(sub)
    md, js = save_plan(plan, tmp_path)
    assert md.exists() and js.exists()
    results = [QueryResult(source_key="zxgk", subject_name="张三", found=True, summary="被列入失信名单")]
    arch = archive_results(results, tmp_path, "张三")
    assert arch.exists()
    assert "失信" in arch.read_text(encoding="utf-8")


def test_plan_json_roundtrip() -> None:
    plan = build_query_plan(Subject(name="张三"))
    s = plan.to_json()
    assert '"name": "张三"' in s
    assert '"subject_type": "person"' in s


# ── FB-6 L2（浏览器辅助/人在环）测试 ──
from acquisition.browser_assist import (  # noqa: E402
    BrowserAssistConfig, build_query_instruction, l2_available, run_l2_query,
)
from acquisition.sources_registry import get_source  # noqa: E402


def test_l2_instruction_has_humanloop_guard() -> None:
    src = get_source("zxgk")
    ins = build_query_instruction(src, "张三")
    # 必须包含"不绕过验证码 + 遇验证码停下等人工"的安全约束
    assert "验证码" in ins
    assert "停止" in ins or "暂停" in ins or "手动完成" in ins
    assert "张三" in ins


def test_l2_degrades_without_browseruse() -> None:
    # 沙箱无 browser_use → 应降级返回指引而非报错
    src = get_source("zxgk")
    r = run_l2_query(src, "张三")
    if not l2_available():
        assert r.found is False
        assert "browser-use" in r.summary
        assert r.source_url == src.base_url


def test_l2_config_defaults_safe() -> None:
    cfg = BrowserAssistConfig()
    assert cfg.headless is False        # 必须显示窗口供人工接管
    assert cfg.pause_on_captcha is True
    assert "4000" in cfg.llm_base_url   # 走本地 LiteLLM 网关

# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-12 00:50:00 CST
"""debt-collection BUILD 模块测试（沙箱可跑通：纯逻辑+SQLite）。"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from debt import compliance, intel, ledger  # noqa: E402
from debt.models import (  # noqa: E402
    Debt, DebtNature, DebtStage, Intel, IntelCredibility, Store, mask_id,
)
from debt.timeline import build_timeline, prescription_status  # noqa: E402


# ── models ──
def test_mask_id() -> None:
    assert mask_id("330102199001011234") == "330***********1234"
    assert mask_id("123") == "***"


def test_debt_outstanding() -> None:
    d = Debt(debtor_name="张三", amount=50000, repaid=20000)
    assert d.outstanding == 30000


# ── ledger (SQLite) ──
def _store(tmp_path) -> Store:
    return Store(db_path=tmp_path / "t.db")


def test_ledger_crud_and_8_debts(tmp_path) -> None:
    s = _store(tmp_path)
    for i in range(8):  # AC-1：≥8 笔
        ledger.add_debt(s, Debt(debtor_name=f"债务人{i}", amount=10000 + i))
    debts = ledger.list_debts(s)
    assert len(debts) == 8
    assert ledger.total_outstanding(s) == round(sum(10000 + i for i in range(8)), 2)
    s.close()


def test_ledger_repayment_and_stage(tmp_path) -> None:
    s = _store(tmp_path)
    did = ledger.add_debt(s, Debt(debtor_name="张三", amount=50000))
    ledger.record_repayment(s, did, 20000)
    ledger.update_stage(s, did, DebtStage.LITIGATION)
    d = ledger.get_debt(s, did)
    assert d.outstanding == 30000 and d.stage == DebtStage.LITIGATION
    s.close()


# ── timeline: 诉讼时效 ──
def test_prescription_ok() -> None:
    today = date(2026, 6, 12)
    d = Debt(debtor_name="张三", amount=1, due_date="2025-01-01")
    st = prescription_status(d, today=today)
    assert st.level == "ok" and not st.expired


def test_prescription_expired() -> None:
    today = date(2026, 6, 12)
    d = Debt(debtor_name="张三", amount=1, due_date="2020-01-01")
    st = prescription_status(d, today=today)
    assert st.expired and st.level == "expired"


def test_prescription_urgent() -> None:
    today = date(2026, 6, 12)
    # 起算日使 deadline 在 20 天后
    start = today - timedelta(days=365 * 3 - 20)
    d = Debt(debtor_name="张三", amount=1, due_date=start.isoformat())
    st = prescription_status(d, today=today)
    assert st.level == "urgent"


def test_prescription_last_contact_overrides_due() -> None:
    today = date(2026, 6, 12)
    # 约定还款很久以前(本应过期)，但最后催收较近 → 时效重新起算未过期
    d = Debt(debtor_name="张三", amount=1, due_date="2019-01-01", last_contact_date="2025-06-01")
    st = prescription_status(d, today=today)
    assert not st.expired


def test_prescription_missing_dates() -> None:
    st = prescription_status(Debt(debtor_name="张三", amount=1))
    assert st.level == "unknown"


# ── intel + timeline 聚合 ──
def test_intel_and_timeline(tmp_path) -> None:
    s = _store(tmp_path)
    did = ledger.add_debt(s, Debt(debtor_name="张三", amount=50000,
                                  lend_date="2024-01-01", due_date="2024-07-01"))
    intel.add_intel(s, Intel(debt_id=did, content="债务人当选村支书",
                             source="朋友", credibility=IntelCredibility.MEDIUM, created_at="2026-05-01"))
    intel.add_intel(s, Intel(debt_id=did, content="无关八卦", source="网络",
                             affects_strategy=False, created_at="2026-05-02"))
    items = intel.list_intel(s, did)
    assert len(items) == 2
    affecting = intel.strategy_affecting_intel(s, did)
    assert len(affecting) == 1 and "村支书" in affecting[0].content
    # 时间线聚合并排序
    d = ledger.get_debt(s, did)
    tl = build_timeline(d, items)
    kinds = [e.kind for e in tl]
    assert "debt" in kinds and "intel" in kinds
    assert tl == sorted(tl, key=lambda e: e.when or "9999-99-99")
    s.close()


# ── compliance（红线守门人）──
def test_compliance_blocks_illegal() -> None:
    r = compliance.check_text("给他发威胁短信，爆通讯录，查银行流水")
    assert not r.passed
    assert any("威胁" in v for v in r.violations)
    assert any("爆通讯录" in v for v in r.violations)
    assert any("流水" in v for v in r.violations)


def test_compliance_allows_legal_pressure_with_caution() -> None:
    # 依法向单位/上级反映真实欠债 = 正当维权，放行但给注意提示
    r = compliance.check_text("先告知利弊，若不还则依法向其任职单位和上级反映真实欠债事实")
    assert r.passed                      # 无违法词
    assert any("单位" in c or "上级" in c for c in r.cautions)  # 有合规注意


def test_compliance_clean_text() -> None:
    r = compliance.check_text("整理借条和转账记录，发起诉前财产保全")
    assert r.passed and not r.cautions


# ── knowledge（法务知识防幻觉）──
def test_knowledge_points() -> None:
    from debt import knowledge
    pts = knowledge.get_points("诉讼时效", "财产保全")
    assert len(pts) == 2
    ctx = knowledge.legal_context_for_strategy()
    assert "民法典" in ctx and "勿编造" in ctx


# ── llm_client 降级（沙箱无网关）──
def test_llm_client_degrades() -> None:
    from debt.llm_client import available, chat
    # 沙箱无网关 → available False，chat 返回 None（不报错）
    assert available() in (True, False)   # 不抛异常即可
    # chat 在无网关时返回 None
    if not available():
        assert chat("hi") is None


# ── strategy 离线兜底 + 合规 ──
def test_strategy_offline_report() -> None:
    from debt.strategy import generate_report
    d = Debt(debtor_name="张三", amount=50000, due_date="2025-01-01",
             evidence=["借条", "转账记录"])
    intels = [Intel(debt_id=1, content="债务人当选村支书", source="朋友",
                    credibility=IntelCredibility.MEDIUM, created_at="2026-05-01")]
    rep = generate_report(d, intels)
    assert rep.debtor_name == "张三"
    assert rep.model_used in ("offline-template", "cloud/glm-primary", "local/primary")
    assert "执行可行性" in rep.body or "执行" in rep.body
    assert rep.compliance_passed   # 离线模板不含违法词


# ── integrations 接工厂能力 ──
def test_integration_acquisition() -> None:
    from debt.integrations import build_acquisition_plan
    res = build_acquisition_plan("张三", region="杭州", out_dir="runtime/test_acq")
    # 工厂 acquisition 存在 → ok 且有 tasks
    if res["ok"]:
        assert len(res["tasks"]) >= 1
        assert any("执行" in t["source"] or "裁判" in t["source"] for t in res["tasks"])


# ── CLI 冒烟（add→list→intel→report 全链路）──
def test_cli_smoke(tmp_path, capsys) -> None:
    from debt.cli import main
    db = str(tmp_path / "cli.db")
    assert main(["--db", db, "add", "张三", "50000", "--due", "2025-01-01", "--evidence", "借条,转账"]) == 0
    assert main(["--db", db, "list"]) == 0
    out = capsys.readouterr().out
    assert "张三" in out
    assert main(["--db", db, "intel", "1", "债务人当选村支书", "--source", "朋友"]) == 0
    assert main(["--db", db, "timeline", "1"]) == 0
    assert main(["--db", db, "report", "1"]) == 0
    out2 = capsys.readouterr().out
    assert "合规" in out2

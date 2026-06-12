# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-12 00:50:00 CST
"""债务台账 CRUD（F1，AC-1：支持 ≥8 笔）。"""
from __future__ import annotations

import json

from debt.models import Debt, DebtNature, DebtStage, Store


def _row_to_debt(row: dict) -> Debt:
    return Debt(
        id=row["id"], debtor_name=row["debtor_name"], amount=row["amount"],
        nature=DebtNature(row["nature"]) if row["nature"] else DebtNature.PRIVATE_LOAN,
        debtor_id=row["debtor_id"] or "", debtor_region=row["debtor_region"] or "",
        lend_date=row["lend_date"] or "", due_date=row["due_date"] or "",
        last_contact_date=row["last_contact_date"] or "", repaid=row["repaid"] or 0.0,
        stage=DebtStage(row["stage"]) if row["stage"] else DebtStage.NEGOTIATION,
        evidence=json.loads(row["evidence"]) if row["evidence"] else [],
        note=row["note"] or "",
    )


def add_debt(store: Store, debt: Debt) -> int:
    """新增一笔债务，返回 id。"""
    cur = store.conn.execute(
        """INSERT INTO debt(debtor_name,amount,nature,debtor_id,debtor_region,
           lend_date,due_date,last_contact_date,repaid,stage,evidence,note)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
        (debt.debtor_name, debt.amount, debt.nature.value, debt.debtor_id,
         debt.debtor_region, debt.lend_date, debt.due_date, debt.last_contact_date,
         debt.repaid, debt.stage.value, json.dumps(debt.evidence, ensure_ascii=False), debt.note),
    )
    store.conn.commit()
    return int(cur.lastrowid)


def get_debt(store: Store, debt_id: int) -> Debt | None:
    row = store.conn.execute("SELECT * FROM debt WHERE id=?", (debt_id,)).fetchone()
    return _row_to_debt(dict(row)) if row else None


def list_debts(store: Store) -> list[Debt]:
    rows = store.conn.execute("SELECT * FROM debt ORDER BY id").fetchall()
    return [_row_to_debt(dict(r)) for r in rows]


def update_stage(store: Store, debt_id: int, stage: DebtStage) -> None:
    store.conn.execute("UPDATE debt SET stage=? WHERE id=?", (stage.value, debt_id))
    store.conn.commit()


def record_repayment(store: Store, debt_id: int, amount: float) -> None:
    """记录一笔还款（累加）。"""
    store.conn.execute("UPDATE debt SET repaid=repaid+? WHERE id=?", (amount, debt_id))
    store.conn.commit()


def total_outstanding(store: Store) -> float:
    """所有债务未还总额。"""
    return round(sum(d.outstanding for d in list_debts(store)), 2)

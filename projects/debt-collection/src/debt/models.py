# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-12 00:50:00 CST
"""数据模型：债务 / 证据 / 情报 / 策略报告（含 SQLite 存储）。

设计：纯本地 SQLite（ADR-001/005），敏感字段(身份证号)展示时脱敏。
模型用 dataclass，存储用标准库 sqlite3（零三方依赖）。
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any


class DebtNature(str, Enum):
    """债务性质（不同性质举证/法律路径不同）。"""

    PRIVATE_LOAN = "private_loan"   # 民间借贷
    BUSINESS = "business"           # 买卖/货款/工程款等合同欠款
    OTHER = "other"


class DebtStage(str, Enum):
    """讨债阶段。"""

    NEGOTIATION = "negotiation"     # 协商
    LAWYER_LETTER = "lawyer_letter" # 律师函
    PAYMENT_ORDER = "payment_order" # 支付令
    LITIGATION = "litigation"       # 诉讼
    EXECUTION = "execution"         # 执行
    CLOSED = "closed"               # 已了结


class IntelCredibility(str, Enum):
    """情报可信度（关联 sources.yaml 的来源分级思路）。"""

    HIGH = "high"        # 官方/亲见
    MEDIUM = "medium"    # 朋友转述/间接
    LOW = "low"          # 道听途说


def mask_id(id_number: str) -> str:
    """身份证号脱敏：保留前3后4，中间打码（展示用，ADR-005）。"""
    s = (id_number or "").strip()
    if len(s) <= 7:
        return "*" * len(s)
    return s[:3] + "*" * (len(s) - 7) + s[-4:]


@dataclass
class Debt:
    """一笔债务。"""

    debtor_name: str
    amount: float                       # 本金（元）
    nature: DebtNature = DebtNature.PRIVATE_LOAN
    debtor_id: str = ""                 # 身份证号/统一社会信用代码（敏感，脱敏展示）
    debtor_region: str = ""
    lend_date: str = ""                 # 借出/账期起算日 YYYY-MM-DD
    due_date: str = ""                  # 约定还款日 YYYY-MM-DD
    last_contact_date: str = ""         # 最后一次催收/对方承诺还款日（影响时效中断）
    repaid: float = 0.0                 # 已还金额
    stage: DebtStage = DebtStage.NEGOTIATION
    evidence: list[str] = field(default_factory=list)  # 证据清单(借条/转账记录/聊天…)
    note: str = ""
    id: int | None = None

    @property
    def outstanding(self) -> float:
        """未还金额。"""
        return round(self.amount - self.repaid, 2)


@dataclass
class Intel:
    """一条情报（ADR-006：动态案件博弈）。"""

    debt_id: int
    content: str                        # 情报内容，如"债务人当选村支书"
    source: str = ""                    # 来源：朋友/微信/官方查询/媒体…
    credibility: IntelCredibility = IntelCredibility.MEDIUM
    affects_strategy: bool = True       # 是否影响策略（触发重算）
    created_at: str = ""                # YYYY-MM-DD
    id: int | None = None


@dataclass
class TimelineEvent:
    """时间线事件（聚合视图用，不单独建表，由各表汇总）。"""

    when: str
    kind: str           # debt/contact/intel/acquisition/stage_change
    summary: str


# ─────────────────────── SQLite 存储 ───────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS debt (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    debtor_name TEXT NOT NULL, amount REAL NOT NULL, nature TEXT,
    debtor_id TEXT, debtor_region TEXT, lend_date TEXT, due_date TEXT,
    last_contact_date TEXT, repaid REAL DEFAULT 0, stage TEXT,
    evidence TEXT, note TEXT
);
CREATE TABLE IF NOT EXISTS intel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    debt_id INTEGER NOT NULL, content TEXT NOT NULL, source TEXT,
    credibility TEXT, affects_strategy INTEGER DEFAULT 1, created_at TEXT,
    FOREIGN KEY(debt_id) REFERENCES debt(id)
);
"""


class Store:
    """SQLite 存储封装。默认本地文件，纯本地不外传。"""

    def __init__(self, db_path: str | Path = "runtime/debt.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # 上下文管理，便于 with 使用
    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

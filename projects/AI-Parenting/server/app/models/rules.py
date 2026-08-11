# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
#
# app/models/rules.py —— 规则、家庭知识、审计、同步状态 ORM。
# 依据：ENGINEERING_DESIGN §6.1（family_knowledge/evidence_policy/audit_log/sync_state）、§6.2（约束）；
#       §22.2（audit_log 不可删除）；TASK_BACKLOG APC-T004。
# 设计：evidence_policy (policy_type,region,version) UNIQUE + effective_to IS NULL 当前生效；
#       audit_log append-only（不继承 SoftDeleteMixin，迁移层 REVOKE UPDATE/DELETE）；
#       sync_state client_id PK；family_knowledge 版本化（M2 家庭偏好）。

"""规则、家庭知识、审计、同步状态 ORM。

表结构 SSOT：``ENGINEERING_DESIGN §6.1`` + ``§6.2``（约束）+ ``§22.2``（audit_log 不可删除）。
- ``family_knowledge``：M2 家庭偏好（family_id + key + value jsonb + version）。
- ``evidence_policy``：规则版本化（policy_type,region,version）UNIQUE，effective_to IS NULL 当前生效。
- ``audit_log``：append-only（迁移层 REVOKE UPDATE/DELETE，不继承软删除）。
- ``sync_state``：同步状态（client_id PK + last_seen_at + pending_count）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, ULIDPrimaryKey


class FamilyKnowledge(Base, ULIDPrimaryKey, TimestampMixin):
    """家庭知识（§6.1：M2 家庭偏好，family_id + key + value jsonb + version）。"""

    __tablename__ = "family_knowledge"

    family_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("family.id", ondelete="CASCADE"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("family_id", "key", name="uq_family_knowledge_family_key"),
        Index("ix_family_knowledge_family_id", "family_id"),
    )


class EvidencePolicy(Base, ULIDPrimaryKey, TimestampMixin):
    """证据规则（§6.1/§6.2：规则版本化，policy_type+region+version UNIQUE，effective_to IS NULL 当前生效）。

    规则库变更强制递增 version（架构 §18）；不可软删除（保留历史版本）。
    """

    __tablename__ = "evidence_policy"

    policy_type: Mapped[str] = mapped_column(String(64), nullable=False)
    region: Mapped[str] = mapped_column(String(8), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_text: Mapped[str] = mapped_column(nullable=False)
    display_text: Mapped[str] = mapped_column(nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "policy_type", "region", "version", name="uq_evidence_policy_type_region_version"
        ),
        Index("ix_evidence_policy_type_region", "policy_type", "region"),
    )


class AuditLog(Base, ULIDPrimaryKey):
    """审计日志（§6.1/§22.2：append-only，迁移层 REVOKE UPDATE/DELETE 强制不可删除）。

    不继承 TimestampMixin（用 ts 单列）/ SoftDeleteMixin（不可删除）。
    任何 mutating 操作用 @audit 留痕（架构 §14.5）。
    """

    __tablename__ = "audit_log"

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource: Mapped[str] = mapped_column(String(255), nullable=False)
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    rule_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    llm_call_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_audit_log_ts", "ts"),
        Index("ix_audit_log_actor_action", "actor", "action"),
        Index("ix_audit_log_resource", "resource"),
    )


class SyncState(Base):
    """同步状态（§6.1：client_id PK + last_seen_at + pending_count）。

    跟踪各客户端（Android/设备）同步进度，PowerSync 上行对账。
    """

    __tablename__ = "sync_state"

    client_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pending_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


__all__ = ["AuditLog", "EvidencePolicy", "FamilyKnowledge", "SyncState"]

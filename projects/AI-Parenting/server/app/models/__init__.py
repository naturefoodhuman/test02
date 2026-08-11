# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-10 00:00:00
#
# app/models/__init__.py —— SQLAlchemy ORM 模型聚合。
# 依据：ENGINEERING_DESIGN §6（数据模型）；ARCHITECTURE_FINAL §6/§7；TASK_BACKLOG APC-T004。
# 设计：所有 ORM 模型共享同一 ``Base``（``DeclarativeBase``），供 Alembic autogenerate 与
#       ``migrations/env.py`` 的 ``target_metadata`` 使用。按领域分文件，本 __init__ 聚合导出。
# 表结构 SSOT：ENGINEERING_DESIGN §6.1（核心实体与表）+ §5.1（ObservationEvent 数据契约）。

"""SQLAlchemy ORM 模型聚合。

所有模型共享同一 ``Base``（``DeclarativeBase``）。按领域分文件，
本模块聚合导出，供 Alembic ``env.py`` 的 ``target_metadata = Base.metadata`` 使用。

表结构 SSOT：``ENGINEERING_DESIGN §6.1``（核心实体与表）+ ``§5.1``（ObservationEvent 数据契约）。
"""

from .base import Base
from .core import Baby, Device, Family, User
from .derived import Alert, AlertDelivery, CameraEvent, DerivedBabyState, SensorEvent, SleepSession
from .events import ObservationEvent
from .logs import (
    DiaperLog,
    FeedingLog,
    GrowthLog,
    JaundicePhoto,
    MediaAsset,
    MedicationLog,
    MilestoneLog,
    SleepLog,
    SolidFoodLog,
    SupplementLog,
    SymptomEvent,
    TemperatureLog,
    VaccineRecord,
)
from .rules import AuditLog, EvidencePolicy, FamilyKnowledge, SyncState

__all__ = [
    "Alert",
    "AlertDelivery",
    "AuditLog",
    "Baby",
    "Base",
    "CameraEvent",
    "DerivedBabyState",
    "Device",
    "DiaperLog",
    "EvidencePolicy",
    "Family",
    "FamilyKnowledge",
    "FeedingLog",
    "GrowthLog",
    "JaundicePhoto",
    "MediaAsset",
    "MedicationLog",
    "MilestoneLog",
    "ObservationEvent",
    "SensorEvent",
    "SleepLog",
    "SleepSession",
    "SolidFoodLog",
    "SupplementLog",
    "SymptomEvent",
    "SyncState",
    "TemperatureLog",
    "User",
    "VaccineRecord",
]

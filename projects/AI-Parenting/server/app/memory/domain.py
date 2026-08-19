# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-19 00:00:00
#
# app/memory/domain.py —— 五层长期记忆领域类型（APC-T026）。
# 依据：ENGINEERING_DESIGN §5.9（MemoryStore Protocol：m1/m2/m3/m4/m5_search）；
#       ARCHITECTURE_FINAL §6.5（长期记忆五层，源自 PRD §9）；§4.3（健康类回答前
#       必须注入：日龄、当前体重、体重百分位、近72h记录、家庭规则、过敏史、规则版本）。
# 设计：领域层纯数据契约 + Protocol，不感知 HTTP/DB（架构 §5：Protocol + dataclass）。
#       M1/M2/M3/M4 优先结构化查询（PG/FamilyKnowledge/派生状态），仅 M5 用少量向量（Local RAG）。
# 边界：MemoryStore 只读上下文，不产生告警等级、不做医疗判断、不写 DB（写入由各域 service 负责）。
#       M5 复用工厂 Local RAG（adapter 层注入，不复制实现，架构 §6.5/§7）。

"""五层长期记忆领域类型（APC-T026）。

架构（ENGINEERING_DESIGN §5.9 / ARCHITECTURE_FINAL §6.5）：
长期记忆分五层，Orchestrator 在健康类回答前必须注入完整上下文（PRD §9）。

    M1 硬事实      —— PostgreSQL 关系型（baby 表：日龄/体重/性别/过敏/接种地区）。
                       不允许 LLM 猜测（架构 §6.5）。
    M2 家庭偏好    —— FamilyKnowledge 结构化（family_knowledge 表 key/value）。
    M3 行为基线    —— 结构化 + 派生（近 N 天趋势，复用 state_engine 派生指标）。
    M4 短期上下文  —— 派生状态（近 72h 事件 + DerivedBabyState）。
    M5 纠错记忆    —— 结构化 + 少量向量（Local RAG，复用工厂 RAG，自适应调阈）。

边界：MemoryStore 只读，不产生告警等级、不做医疗判断、不写 DB。M5 经 adapter 复用
工厂 Local RAG（架构 §6.5/§7），不复制实现。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class HardFacts:
    """M1 硬事实（PG 关系型，架构 §6.5）。

    不允许 LLM 猜测——这些字段必须来自权威 PG 数据（baby 表）。Orchestrator 注入
    健康类上下文时必须包含日龄、当前体重、性别、过敏史、接种地区（PRD §9）。

    ``age_days``：日龄（now - birth_date 的天数，int 向下取整）。
    ``current_weight_kg``：当前体重（kg，baby.current_weight_g / 1000）；无记录为 None。
    ``current_weight_at``：当前体重记录时间；无记录为 None（用于判断体重时效，T020 用药校验）。
    ``gestational_age_weeks`` / ``is_preterm``：孕周与早产标记（用药/疫苗基线参考）。
    ``birth_weight_g``：出生体重（g）。
    ``sex``：性别（male/female/None）。
    ``vaccine_region``：接种地区（默认 CN，T022 疫苗规则用）。
    ``allergies``：过敏史（baby.allergies jsonb 原样透传，结构由调用方解读）。
    ``birth_date``：出生日期（用于精确日龄计算，T022/T023 规则输入）。
    """

    baby_id: str
    family_id: str
    birth_date: date
    age_days: int
    sex: str | None
    current_weight_kg: float | None
    current_weight_at: datetime | None
    birth_weight_g: int | None
    gestational_age_weeks: int | None
    is_preterm: bool
    vaccine_region: str
    allergies: dict[str, Any] | None


@dataclass(frozen=True)
class FamilyPrefs:
    """M2 家庭偏好（FamilyKnowledge 结构化，架构 §6.5）。

    family_knowledge 表 key → value jsonb 映射。Orchestrator 注入"家庭规则"上下文
    （PRD §9）。常见 key：feeding_schedule / sleep_routine / care_preferences 等，
    具体语义由 FamilyMemory Copilot（T030）写入，本层只读透传。
    """

    family_id: str
    preferences: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Baseline:
    """M3 行为基线（结构化 + 派生，架构 §6.5）。

    近 ``window_days`` 天的趋势基线，供趋势预警与"是否偏离基线"判断（T021 阈值规则）。
    P0 复用 state_engine 派生指标做简化基线（近 N 天日均奶量/睡眠/尿布/体温），
    完整基线建模留待 V1。本层只读，不产生告警。

    ``window_days``：基线窗口天数。
    ``avg_volume_ml_per_day``：窗口内日均喂奶量（ml）；无数据为 None。
    ``avg_sleep_hours_per_day``：窗口内日均睡眠（小时）；无数据为 None。
    ``avg_wet_diapers_per_day``：窗口内日均湿尿布数；无数据为 None。
    ``avg_dirty_diapers_per_day``：窗口内日均脏尿布数；无数据为 None。
    ``max_temperature_c``：窗口内最高体温（℃）；无数据为 None。
    ``sample_days``：窗口内实际有数据的天数（用于判断基线可信度）。
    """

    baby_id: str
    window_days: int
    avg_volume_ml_per_day: float | None
    avg_sleep_hours_per_day: float | None
    avg_wet_diapers_per_day: float | None
    avg_dirty_diapers_per_day: float | None
    max_temperature_c: float | None
    sample_days: int


@dataclass(frozen=True)
class ShortContext:
    """M4 短期上下文（派生状态，近 72h，架构 §6.5）。

    临时推理用。承载近 72h 事件摘要 + 当前 DerivedBabyState 快照（T016 产出）。
    Orchestrator 健康类回答前必须注入"近 72h 症状/用药/接种"（PRD §9）。

    ``window_hours``：短期窗口小时数（默认 72）。
    ``recent_events``：窗口内未删除事件摘要（event_type + start_time + 关键 payload 字段）。
    ``derived_state``：当前 DerivedBabyState 快照（T016 snapshot，None 表示无快照）。
    """

    baby_id: str
    window_hours: int
    recent_events: list[dict[str, Any]] = field(default_factory=list)
    derived_state: dict[str, Any] | None = None


@dataclass(frozen=True)
class Correction:
    """M5 纠错记忆条目（结构化 + 少量向量，架构 §6.5）。

    自适应调阈用。承载历史纠错反馈（alert feedback / 误报修正），供 Local RAG 检索
    相似场景的过往修正。T031 alert feedback 写入，本层只读检索。

    ``id``：纠错记录标识。
    ``text``：纠错描述（供 RAG 检索的文本）。
    ``metadata``：结构化元数据（alert_type/feedback/调整后的阈值等）。
    ``score``：检索相似度分数（RAG 返回，0-1）。
    """

    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


@dataclass(frozen=True)
class MemorySnapshot:
    """五层记忆聚合快照（APC-T026）。

    Orchestrator 一次性获取完整 CopilotContext 所需 memory（TASK_BACKLOG APC-T026 验收）。
    健康类回答前必须注入完整五层（PRD §9 / 架构 §4.3）。

    ``rule_version``：相关规则版本占位（PRD §9 要求注入"相关规则版本"；
        P0 占位 None，T019 EvidencePolicy get_current 接入后填充）。
    """

    hard_facts: HardFacts | None
    family_prefs: FamilyPrefs | None
    baseline: Baseline | None
    short_context: ShortContext | None
    corrections: list[Correction] = field(default_factory=list)
    rule_version: str | None = None


@runtime_checkable
class MemoryStore(Protocol):
    """五层长期记忆读写协议（ENGINEERING_DESIGN §5.9）。

    生命周期：请求作用域（依赖 AsyncSession）；Orchestrator 经此一次性获取
    MemorySnapshot（架构 §4.3 健康类回答前注入完整上下文）。

    M1/M2/M3/M4 优先结构化查询（PG/FamilyKnowledge/派生状态）；M5 经 adapter
    复用工厂 Local RAG（架构 §6.5），不复制实现。
    """

    async def m1(self, baby_id: str) -> HardFacts | None:
        """M1 硬事实（PG 关系型，baby 表）。"""
        ...

    async def m2(self, family_id: str) -> FamilyPrefs:
        """M2 家庭偏好（FamilyKnowledge 结构化）。"""
        ...

    async def m3(self, baby_id: str, window_days: int = 14) -> Baseline | None:
        """M3 行为基线（近 window_days 天趋势，默认 14 天）。"""
        ...

    async def m4(self, baby_id: str, window_hours: int = 72) -> ShortContext:
        """M4 短期上下文（近 window_hours 小时，默认 72h）。"""
        ...

    async def m5_search(self, query: str, k: int = 5) -> list[Correction]:
        """M5 纠错记忆检索（Local RAG，复用工厂）。"""
        ...


@runtime_checkable
class CorrectionStore(Protocol):
    """M5 纠错记忆读写协议（APC-T026，T031 alert feedback 接入用）。

    P0 由 FakeRagStore 内存实现支撑测试；T031 接入真实 alert feedback 后经
    Local RAG adapter 持久化。``search`` 供 MemoryStore.m5_search 检索；
    ``add_correction`` 供 T031 写入。两者同一协议，避免 T026 提前耦合 T031。
    """

    async def add_correction(self, correction: Correction) -> None:
        """追加一条纠错记忆（M5，供后续 RAG 检索）。"""
        ...

    async def search(self, query: str, k: int = 5) -> list[Correction]:
        """检索相关纠错记忆（关键词/向量相似，返回 top-k，带 score）。"""
        ...


__all__ = [
    "Baseline",
    "Correction",
    "CorrectionStore",
    "FamilyPrefs",
    "HardFacts",
    "MemorySnapshot",
    "MemoryStore",
    "ShortContext",
]

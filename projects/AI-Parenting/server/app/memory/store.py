# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-19 00:00:00
#
# app/memory/store.py —— 五层记忆 PG 实现（APC-T026）。
# 依据：ENGINEERING_DESIGN §5.9（MemoryStore Protocol）；ARCHITECTURE_FINAL §6.5（五层）；
#       §4.3（健康类回答前注入：日龄/体重/百分位/近72h/家庭规则/过敏史/规则版本）；
#       §6.1（baby/family_knowledge/derived_baby_state/observation_event 表）。
# 设计：SqlAlchemyMemoryStore 请求作用域（依赖 AsyncSession），M1/M2/M3/M4 结构化查询 PG，
#       M5 经 rag_adapter 复用工厂 Local RAG（不复制实现）。
# 边界：只读上下文，不产生告警等级、不做医疗判断、不写 DB。日龄由注入 Clock 计算（可测）。
#
# 注：M3/M4 直接查 observation_event（事件 SSOT，含 normalized_payload + start_time），
#     而非各 *_log 派生表——除 feeding_log 外其余 log 表为最小结构（无 started_at 列），
#     事件本身已含 start_time 与 normalized_payload，是趋势/窗口计算的权威源（架构 §6.2）。

"""五层长期记忆 PG 实现（APC-T026）。

``SqlAlchemyMemoryStore`` 实现 ``MemoryStore`` 协议（ENGINEERING_DESIGN §5.9）：

- M1 硬事实：读 ``baby`` 表（birth_date/weight/sex/allergies/vaccine_region/gestational），
  日龄由注入 ``Clock`` 计算（now - birth_date，测试可注入 FixedClock）。
- M2 家庭偏好：读 ``family_knowledge`` 表（family_id + key + value jsonb），聚合为 dict。
- M3 行为基线：读近 ``window_days`` 天未删除 ``observation_event``（feeding/diaper/sleep/
  temperature），从 normalized_payload 取值计算日均指标（P0 简化基线，完整建模留 V1）。
- M4 短期上下文：读近 ``window_hours`` 小时未删除 ``observation_event`` + 当前
  ``derived_baby_state.snapshot``（T016 产出）。
- M5 纠错记忆：经 ``rag_adapter`` 检索（Fake/Forge），不复制工厂实现。

只读，不写 DB、不产生告警等级、不做医疗判断（架构 §6.5 边界）。
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.clock import Clock
from ..models.core import Baby
from ..models.derived import DerivedBabyState as DerivedOrm
from ..models.events import ObservationEvent as EventOrm
from ..models.rules import FamilyKnowledge
from .domain import Baseline, FamilyPrefs, HardFacts, ShortContext
from .rag_adapter import FakeRagStore

if TYPE_CHECKING:
    from .domain import Correction, CorrectionStore


def _age_days(birth_date: Any, now: Any) -> int:
    """日龄 = (now.date() - birth_date).days，向下取整（不小于 0）。"""
    today = now.astimezone().date() if now.tzinfo else now.date()
    return max(0, (today - birth_date).days)


class SqlAlchemyMemoryStore:
    """五层记忆 PG 实现（APC-T026，请求作用域）。

    构造注入 ``AsyncSession``（请求作用域）、``Clock``（日龄计算可测）、
    ``correction_store``（M5 RAG adapter，默认 FakeRagStore）。
    """

    def __init__(
        self,
        session: AsyncSession,
        clock: Clock,
        correction_store: CorrectionStore | None = None,
    ) -> None:
        self._session = session
        self._clock = clock
        self._correction_store = correction_store or FakeRagStore()

    # ---- M1 硬事实 ----

    async def m1(self, baby_id: str) -> HardFacts | None:
        baby = (
            await self._session.execute(select(Baby).where(Baby.id == baby_id))
        ).scalar_one_or_none()
        if baby is None:
            return None
        now = self._clock.now()
        current_weight_kg = (
            float(baby.current_weight_g) / 1000.0 if baby.current_weight_g is not None else None
        )
        return HardFacts(
            baby_id=baby.id,
            family_id=baby.family_id,
            birth_date=baby.birth_date,
            age_days=_age_days(baby.birth_date, now),
            sex=baby.sex,
            current_weight_kg=current_weight_kg,
            current_weight_at=baby.current_weight_at,
            birth_weight_g=baby.birth_weight_g,
            gestational_age_weeks=baby.gestational_age_weeks,
            is_preterm=baby.is_preterm,
            vaccine_region=baby.vaccine_region,
            allergies=baby.allergies,
        )

    # ---- M2 家庭偏好 ----

    async def m2(self, family_id: str) -> FamilyPrefs:
        rows = (
            (
                await self._session.execute(
                    select(FamilyKnowledge).where(FamilyKnowledge.family_id == family_id)
                )
            )
            .scalars()
            .all()
        )
        preferences: dict[str, Any] = {}
        for row in rows:
            # value 为 jsonb dict；非 dict 兜底包装。
            val = row.value if isinstance(row.value, dict) else {"raw": row.value}
            preferences[row.key] = val
        return FamilyPrefs(family_id=family_id, preferences=preferences)

    # ---- M3 行为基线 ----

    async def _window_events(self, baby_id: str, event_type: str, since: Any) -> list[EventOrm]:
        """读窗口内某类型未删除事件（按 start_time 升序）。"""
        rows = (
            (
                await self._session.execute(
                    select(EventOrm)
                    .where(
                        EventOrm.baby_id == baby_id,
                        EventOrm.is_deleted.is_(False),
                        EventOrm.event_type == event_type,
                        EventOrm.start_time >= since,
                    )
                    .order_by(EventOrm.start_time.asc())
                )
            )
            .scalars()
            .all()
        )
        return list(rows)

    async def m3(self, baby_id: str, window_days: int = 14) -> Baseline | None:
        now = self._clock.now()
        since = now - timedelta(days=window_days)
        feedings = await self._window_events(baby_id, "feeding", since)
        diapers = await self._window_events(baby_id, "diaper", since)
        sleeps = await self._window_events(baby_id, "sleep", since)
        temps = await self._window_events(baby_id, "temperature", since)

        feed_days = {e.start_time.astimezone().date() for e in feedings if e.start_time}
        sample_days = len(feed_days)

        if not feedings and not diapers and not sleeps and not temps:
            return Baseline(
                baby_id=baby_id,
                window_days=window_days,
                avg_volume_ml_per_day=None,
                avg_sleep_hours_per_day=None,
                avg_wet_diapers_per_day=None,
                avg_dirty_diapers_per_day=None,
                max_temperature_c=None,
                sample_days=0,
            )

        # 日均奶量（窗口内 amount_ml 之和 / window_days）
        total_volume = 0.0
        for e in feedings:
            payload = e.normalized_payload if isinstance(e.normalized_payload, dict) else {}
            amt = payload.get("amount_ml")
            if isinstance(amt, (int, float)):
                total_volume += float(amt)
        avg_volume = total_volume / window_days if feedings else None

        # 尿布日均（窗口内总数 / window_days）
        wet = 0
        dirty = 0
        for e in diapers:
            payload = e.normalized_payload if isinstance(e.normalized_payload, dict) else {}
            dtype = payload.get("type", "")
            if dtype == "wet":
                wet += 1
            elif dtype == "dirty":
                dirty += 1
            elif dtype == "mixed":
                wet += 1
                dirty += 1
        avg_wet = wet / window_days if diapers else None
        avg_dirty = dirty / window_days if diapers else None

        # 睡眠日均（秒数和 / window_days → 小时；未结束 end 取 now）
        sleep_seconds = 0.0
        for e in sleeps:
            end = e.end_time or now
            if end > e.start_time:
                sleep_seconds += (end - e.start_time).total_seconds()
        avg_sleep_hours = (sleep_seconds / window_days) / 3600.0 if sleeps else None

        # 最高温
        max_temp: float | None = None
        for e in temps:
            payload = e.normalized_payload if isinstance(e.normalized_payload, dict) else {}
            val = payload.get("temperature_c") or payload.get("value")
            if isinstance(val, (int, float)):
                max_temp = val if max_temp is None else max(max_temp, float(val))

        return Baseline(
            baby_id=baby_id,
            window_days=window_days,
            avg_volume_ml_per_day=avg_volume,
            avg_sleep_hours_per_day=avg_sleep_hours,
            avg_wet_diapers_per_day=avg_wet,
            avg_dirty_diapers_per_day=avg_dirty,
            max_temperature_c=max_temp,
            sample_days=sample_days,
        )

    # ---- M4 短期上下文 ----

    async def m4(self, baby_id: str, window_hours: int = 72) -> ShortContext:
        now = self._clock.now()
        since = now - timedelta(hours=window_hours)
        events = (
            (
                await self._session.execute(
                    select(EventOrm)
                    .where(
                        EventOrm.baby_id == baby_id,
                        EventOrm.is_deleted.is_(False),
                        EventOrm.start_time >= since,
                    )
                    .order_by(EventOrm.start_time.desc())
                )
            )
            .scalars()
            .all()
        )
        recent_events: list[dict[str, Any]] = [
            {
                "event_id": e.id,
                "event_type": e.event_type,
                "start_time": e.start_time.isoformat() if e.start_time else None,
                "source": e.source,
                "payload": e.normalized_payload if isinstance(e.normalized_payload, dict) else {},
            }
            for e in events
        ]
        # 当前派生快照（T016 产出）
        snap_row = (
            await self._session.execute(select(DerivedOrm).where(DerivedOrm.baby_id == baby_id))
        ).scalar_one_or_none()
        derived_state: dict[str, Any] | None = None
        if snap_row is not None and isinstance(snap_row.snapshot, dict):
            derived_state = snap_row.snapshot
        return ShortContext(
            baby_id=baby_id,
            window_hours=window_hours,
            recent_events=recent_events,
            derived_state=derived_state,
        )

    # ---- M5 纠错记忆 ----

    async def m5_search(self, query: str, k: int = 5) -> list[Correction]:
        return await self._correction_store.search(query, k=k)


__all__ = ["SqlAlchemyMemoryStore"]

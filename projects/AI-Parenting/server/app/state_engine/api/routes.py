# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-16 00:00:00
#
# app/state_engine/api/routes.py —— State API（APC-T016）。
# 依据：ARCHITECTURE_FINAL §15（GET /api/v1/babies/{id}/state → DerivedBabyState）、§10.1；
#       TASK_BACKLOG APC-T016（state API 只读；鉴权后查询 state）。
# 设计：GET /api/v1/babies/{baby_id}/state 只读——鉴权（state:read）+ baby 归属校验
#       （baby.family_id == principal.family_id，否则 404 不泄露存在性）→ 返回最新快照。
#       无快照时触发一次重算（懒重算，T017 接 worker 后由 worker 驱动）。
# 边界：路由只读，不写事件；RBAC 在 AuthService.authorize；baby 归属校验在路由层。

"""State API（APC-T016）。

``GET /api/v1/babies/{baby_id}/state``：只读查询 baby 最新派生快照。
鉴权（``state:read``）+ baby 归属校验（``baby.family_id == principal.family_id``）。
无快照时触发一次懒重算（``StateEngine.recompute``），确保首次查询有数据。
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth.domain import Principal
from ...auth.service.auth_service import AuthService
from ...common.clock import SystemClock
from ...common.errors import NotFoundError
from ...di import get_principal_dep
from ...models.core import Baby
from ..domain import DerivedBabyState
from ..engine import StateEngine
from ..infra import SqlAlchemyEventLoader
from ..snapshot_repo import SqlAlchemySnapshotRepository

router = APIRouter(prefix="/api/v1/babies", tags=["state"])

PrincipalDep = Annotated[Principal, Depends(get_principal_dep)]


# ---- 请求/响应模型 ----


class BabyStateResponse(BaseModel):
    """派生状态响应（DerivedBabyState 投影，架构 §15）。"""

    model_config = ConfigDict(extra="forbid")

    baby_id: str
    computed_at: datetime
    feeding: dict
    diaper: dict
    sleep: dict
    temperature: dict
    supplement: dict
    source_event_range: list[str | None]

    @classmethod
    def from_domain(cls, baby_id: str, state: DerivedBabyState) -> BabyStateResponse:
        snap = state.to_snapshot()
        rng = snap["source_event_range"]
        return cls(
            baby_id=baby_id,
            computed_at=state.computed_at,
            feeding=snap["feeding"],
            diaper=snap["diaper"],
            sleep=snap["sleep"],
            temperature=snap["temperature"],
            supplement=snap["supplement"],
            source_event_range=rng,
        )


# ---- 依赖 ----


async def get_state_engine_dep(
    request: Request,
) -> AsyncGenerator[StateEngine, None]:
    """FastAPI 依赖：按请求构造 StateEngine（请求作用域 session）。

    StateEngine 持有请求级 ``AsyncSession``（EventLoader / SnapshotRepo / EventRepo 共享）；
    ``Clock`` 用 SystemClock（参考时间）。session 在请求结束时关闭。
    """
    from ...db import get_session_factory
    from ...events.infra.repository import SqlAlchemyObservationEventRepository

    factory = get_session_factory()
    async with factory() as session:
        yield StateEngine(
            event_loader=SqlAlchemyEventLoader(session),
            snapshot_repo=SqlAlchemySnapshotRepository(session),
            event_repo=SqlAlchemyObservationEventRepository(session),
            clock=SystemClock(),
        )


StateEngineDep = Annotated[StateEngine, Depends(get_state_engine_dep)]


async def get_request_session_dep(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：请求作用域 session（baby 归属校验用）。"""
    from ...db import get_session_factory

    factory = get_session_factory()
    async with factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_request_session_dep)]


# ---- 路由 ----


async def _check_baby_belongs(
    session: AsyncSession, baby_id: str, family_id: str
) -> None:
    """校验 baby 属于该 family；不存在/不属于则 404（不泄露存在性，§19）。"""
    row = (
        await session.execute(select(Baby).where(Baby.id == baby_id))
    ).scalar_one_or_none()
    if row is None or row.family_id != family_id:
        raise NotFoundError(f"baby {baby_id} not found in your family")


@router.get("/{baby_id}/state", response_model=BabyStateResponse)
async def get_baby_state(
    baby_id: Annotated[str, Path(description="婴儿 ULID")],
    principal: PrincipalDep,
    session: SessionDep,
    engine: StateEngineDep,
) -> BabyStateResponse:
    """查询 baby 最新派生状态（只读，需 state:read；APC-T016）。

    无快照时触发一次懒重算（首次查询有数据）。返回最新 ``DerivedBabyState``。
    """
    AuthService.authorize(principal, "state:read")
    await _check_baby_belongs(session, baby_id, principal.family_id)
    state = await engine.get_state(baby_id)
    if state is None:
        # 无快照 → 懒重算（T017 接 worker 后由 worker 驱动；首次查询兜底）。
        state = await engine.recompute(baby_id)
    return BabyStateResponse.from_domain(baby_id, state)


__all__ = ["router"]

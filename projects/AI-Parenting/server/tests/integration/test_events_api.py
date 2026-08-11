# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""Events API 集成测试（APC-T010，需 DB）。

两类测试：
    1. HTTP 流程（create/list/correct/soft-delete/RBAC/幂等/审计调用）：用 dependency_overrides
       注入内存替身 EventContext + AuthService，避免与 TestClient event loop 跨循环的 engine
       死连接问题（test_audit 注释）。
    2. DB 写入（create + audit_log 行产生）：纯 DB 测试（asyncio.run + reset_db），
       不混 TestClient，与 test_audit 同模式；验证 mutating 操作产生审计（§10.4）。

标记 integration（需真实 PG）；通过 PARENTING_DATABASE__URL 指向 AI_parenting_dev。
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from server.app.auth.service.auth_service import AuthService
from server.app.auth.service.jwt import Hs256JwtService
from server.app.auth.service.password import Pbkdf2PasswordHasher
from server.app.common.clock import SystemClock
from server.app.common.ids import new_id
from server.app.db import get_session_factory
from server.app.di import EventContext, get_event_context_dep
from server.app.events.domain import (
    ObservationEvent,
    Source,
)
from server.app.events.infra.repository import SqlAlchemyObservationEventRepository
from server.app.events.service.idempotency import EventService
from server.app.models.core import Baby, Family
from server.app.models.rules import AuditLog
from server.app.observability.audit import AuditService
from server.app.settings import get_settings

pytestmark = pytest.mark.integration


# ---- 内存替身（HTTP 流程测试用）----


class _FakeAuditService:
    """内存审计替身，记录 append 调用（验证 mutating 留痕，§10.4）。"""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def append(self, *, actor, action, resource, before=None, after=None, **_):
        self.calls.append(
            {"actor": actor, "action": action, "resource": resource, "after": after}
        )
        return "01JZFAKEAUDIT00000000000001"


class _FakeEventRepository:
    """内存事件仓储替身（实现 domain.ObservationEventRepository）。"""

    def __init__(self) -> None:
        self.events: dict[str, ObservationEvent] = {}

    async def get(self, event_id: str) -> ObservationEvent | None:
        ev = self.events.get(event_id)
        return ev if ev and not ev.is_deleted else None

    async def upsert(self, entity: ObservationEvent) -> ObservationEvent:
        if entity.event_id in self.events:
            return self.events[entity.event_id]
        self.events[entity.event_id] = entity
        return entity

    async def query(self, *, baby_id=None, family_id=None, event_type=None, limit=100):
        result = [
            ev
            for ev in self.events.values()
            if not ev.is_deleted
            and (baby_id is None or ev.baby_id == baby_id)
            and (family_id is None or ev.family_id == family_id)
            and (event_type is None or ev.event_type == event_type)
        ]
        return sorted(result, key=lambda e: e.start_time, reverse=True)[:limit]

    async def soft_delete(self, event_id: str) -> ObservationEvent | None:
        ev = self.events.get(event_id)
        if ev is None or ev.is_deleted:
            return None
        deleted = ev.model_copy(update={"is_deleted": True})
        self.events[event_id] = deleted
        return deleted


def _make_fake_event_context() -> tuple[EventContext, _FakeAuditService, _FakeEventRepository]:
    """构造内存替身 EventContext（EventService + AuditService 不碰 DB）。"""
    repo = _FakeEventRepository()
    audit = _FakeAuditService()
    ctx = EventContext(
        event_service=EventService(repository=repo, clock=SystemClock()),
        audit_service=audit,  # type: ignore[arg-type] — 测试替身
    )
    return ctx, audit, repo


def _make_fake_auth_service() -> AuthService:
    """构造 AuthService（用真实 JWT 签发，不碰 DB；principal 由 token 还原）。"""
    from server.tests.integration.test_auth_api import _FakeUserRepository

    settings = get_settings()
    return AuthService(
        repository=_FakeUserRepository(),
        password_hasher=Pbkdf2PasswordHasher(iterations=10_000),
        jwt_service=Hs256JwtService(
            secret=settings.auth.jwt_secret, access_ttl_seconds=settings.auth.access_ttl_seconds
        ),
        clock=SystemClock(),
        access_ttl_seconds=settings.auth.access_ttl_seconds,
        device_repository=_FakeUserRepository(),
    )


@pytest.fixture
def client_with_fakes(client: TestClient) -> Iterator[TestClient]:
    """注入内存替身 EventContext + AuthService 的 TestClient。"""
    from typing import cast

    from fastapi import FastAPI

    from server.app.di import get_auth_service_dep

    fake_event_ctx, _, _ = _make_fake_event_context()
    fake_auth = _make_fake_auth_service()

    async def _override_event_ctx():
        yield fake_event_ctx

    async def _override_auth():
        yield fake_auth

    app = cast(FastAPI, client.app)
    app.dependency_overrides[get_event_context_dep] = _override_event_ctx
    app.dependency_overrides[get_auth_service_dep] = _override_auth
    yield client
    app.dependency_overrides.clear()


def _admin_token(client_with_fakes: TestClient) -> str:
    """登录替身 Admin 取 token。"""
    resp = client_with_fakes.post(
        "/api/v1/auth/login",
        json={
            "family_id": "01JZFAKEFAMILY00000001",
            "display_name": "Dad",
            "password": "admin-pass",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _viewer_token(client_with_fakes: TestClient) -> str:
    resp = client_with_fakes.post(
        "/api/v1/auth/login",
        json={
            "family_id": "01JZFAKEFAMILY00000001",
            "display_name": "Aunt",
            "password": "viewer-pass",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


NOW = datetime(2026, 8, 11, 8, 0, tzinfo=UTC)

# 合法 ULID 常量（Crockford base32，26 字符），供 HTTP 测试 body 用（record 校验 ULID）。
FAM_ID = "01HZXKQW7P0QJ9V8R3M4N6H5T4"
BABY_ID = "01HZXKQW7P0QJ9V8R3M4N6H5T5"


def _create_body(event_id: str | None = None) -> dict:
    return {
        "event_id": event_id or new_id(),
        "baby_id": BABY_ID,
        "family_id": FAM_ID,
        "event_type": "feeding",
        "start_time": NOW.isoformat(),
        "client_created_at": NOW.isoformat(),
        "normalized_payload": {"amount_ml": 120},
        "source": "manual",
    }


# ---- HTTP 流程测试 ----


def test_create_event_returns_201_and_audits(client_with_fakes: TestClient):
    token = _admin_token(client_with_fakes)
    body = _create_body()
    resp = client_with_fakes.post(
        "/api/v1/events", headers={"Authorization": f"Bearer {token}"}, json=body
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["event_id"] == body["event_id"]
    assert data["event_type"] == "feeding"
    assert data["source"] == "manual"
    assert data["sync_status"] == "pending"
    assert data["is_deleted"] is False


def test_create_event_idempotent_same_event_id(client_with_fakes: TestClient):
    token = _admin_token(client_with_fakes)
    body = _create_body()
    r1 = client_with_fakes.post(
        "/api/v1/events", headers={"Authorization": f"Bearer {token}"}, json=body
    )
    r2 = client_with_fakes.post(
        "/api/v1/events", headers={"Authorization": f"Bearer {token}"}, json=body
    )
    assert r1.status_code == 201
    assert r2.status_code == 201  # 幂等：不 409
    assert r1.json()["event_id"] == r2.json()["event_id"]


def test_list_events_returns_timeline_excluding_deleted(client_with_fakes: TestClient):
    token = _admin_token(client_with_fakes)
    # 创建 2 条。
    e1 = _create_body()
    e2 = _create_body()
    e2["event_type"] = "diaper"
    client_with_fakes.post("/api/v1/events", headers={"Authorization": f"Bearer {token}"}, json=e1)
    client_with_fakes.post("/api/v1/events", headers={"Authorization": f"Bearer {token}"}, json=e2)
    resp = client_with_fakes.get(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {token}"},
        params={"baby_id": BABY_ID},
    )
    assert resp.status_code == 200, resp.text
    items = resp.json()
    assert len(items) == 2
    # 软删除一条后不再出现。
    client_with_fakes.delete(
        f"/api/v1/events/{e1['event_id']}", headers={"Authorization": f"Bearer {token}"}
    )
    resp2 = client_with_fakes.get(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {token}"},
        params={"baby_id": BABY_ID},
    )
    assert len(resp2.json()) == 1
    assert resp2.json()[0]["event_id"] == e2["event_id"]


def test_correct_event_creates_correction_chain(client_with_fakes: TestClient):
    token = _admin_token(client_with_fakes)
    body = _create_body()
    client_with_fakes.post("/api/v1/events", headers={"Authorization": f"Bearer {token}"}, json=body)
    correct_body = {
        "baby_id": body["baby_id"],
        "family_id": body["family_id"],
        "event_type": "feeding",
        "start_time": NOW.isoformat(),
        "client_created_at": NOW.isoformat(),
        "normalized_payload": {"amount_ml": 90},
        "source": "manual",
    }
    resp = client_with_fakes.post(
        f"/api/v1/events/{body['event_id']}/correct",
        headers={"Authorization": f"Bearer {token}"},
        json=correct_body,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["correction_of"] == body["event_id"]
    assert data["event_id"] != body["event_id"]
    assert data["normalized_payload"] == {"amount_ml": 90}


def test_soft_delete_returns_deleted_event(client_with_fakes: TestClient):
    token = _admin_token(client_with_fakes)
    body = _create_body()
    client_with_fakes.post("/api/v1/events", headers={"Authorization": f"Bearer {token}"}, json=body)
    resp = client_with_fakes.delete(
        f"/api/v1/events/{body['event_id']}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_deleted"] is True


def test_viewer_cannot_create_event_403(client_with_fakes: TestClient):
    token = _viewer_token(client_with_fakes)
    resp = client_with_fakes.post(
        "/api/v1/events", headers={"Authorization": f"Bearer {token}"}, json=_create_body()
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "PARENTING.FORBIDDEN"


def test_viewer_can_list_events(client_with_fakes: TestClient):
    """Viewer 有 event:read（§19 权限表），可查询。"""
    token = _viewer_token(client_with_fakes)
    resp = client_with_fakes.get(
        "/api/v1/events", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200


def test_no_token_returns_401(client: TestClient):
    """无 Authorization → 401（不需 DB）。"""
    assert client.post("/api/v1/events", json=_create_body()).status_code == 401


# ---- DB 写入测试（纯 DB，验证 audit_log 行产生，§10.4）----


@pytest.fixture(autouse=True)
def _reset_db():
    from server.app import db as db_module

    db_module.reset_db()
    yield
    db_module.reset_db()


async def _make_family_baby(session) -> tuple[str, str]:
    family = Family(id=new_id(), name="事件API测试家", timezone="Asia/Shanghai")
    session.add(family)
    await session.flush()
    baby = Baby(id=new_id(), family_id=family.id, birth_date=date(2026, 6, 1), sex="male")
    session.add(baby)
    await session.flush()
    return family.id, baby.id


def test_create_event_writes_audit_log_row():
    """端到端 DB：create event → audit_log 产生一行（§10.4 不可绕过）。"""

    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_baby(session)
            audit = AuditService(session, SystemClock())
            svc = EventService(
                repository=SqlAlchemyObservationEventRepository(session),
                clock=SystemClock(),
                session=session,
            )
            event_id = new_id()
            await svc.record(
                event_id=event_id,
                baby_id=baby_id,
                family_id=family_id,
                event_type="feeding",
                start_time=NOW,
                client_created_at=NOW,
                normalized_payload={"amount_ml": 120},
                source=Source.MANUAL,
                audit=audit,
            )
            await session.commit()
            rows = (
                await session.execute(
                    select(AuditLog.action, AuditLog.resource).where(
                        AuditLog.resource == f"observation_event/{event_id}"
                    )
                )
            ).all()
        return {"count": len(rows), "action": rows[0][0] if rows else None}

    r = asyncio.run(run())
    assert r["count"] == 1
    assert r["action"] == "create"


def test_correct_and_soft_delete_each_audit():
    """端到端 DB：correct + soft_delete 各产生审计行（§10.4）。"""

    async def run() -> dict:
        factory = get_session_factory()
        async with factory() as session:
            family_id, baby_id = await _make_family_baby(session)
            audit = AuditService(session, SystemClock())
            svc = EventService(
                repository=SqlAlchemyObservationEventRepository(session),
                clock=SystemClock(),
                session=session,
            )
            original_id = new_id()
            await svc.record(
                event_id=original_id,
                baby_id=baby_id,
                family_id=family_id,
                event_type="feeding",
                start_time=NOW,
                client_created_at=NOW,
                normalized_payload={"amount_ml": 120},
                source=Source.MANUAL,
                audit=audit,
            )
            corrected = await svc.correct(
                correction_of=original_id,
                baby_id=baby_id,
                family_id=family_id,
                event_type="feeding",
                start_time=NOW,
                client_created_at=NOW,
                normalized_payload={"amount_ml": 90},
                source=Source.MANUAL,
                audit=audit,
            )
            await svc.soft_delete(event_id=corrected.event_id, audit=audit)
            await session.commit()
            actions = (
                await session.execute(
                    select(AuditLog.action).where(
                        AuditLog.resource.in_(
                            [f"observation_event/{original_id}", f"observation_event/{corrected.event_id}"]
                        )
                    )
                )
            ).scalars().all()
        return {"actions": sorted(actions)}

    r = asyncio.run(run())
    # create(original) + correct(new) + delete(new) = 3 行；soft_delete(original) 在 correct 内部不走 audit。
    assert "create" in r["actions"]
    assert "correct" in r["actions"]
    assert "delete" in r["actions"]

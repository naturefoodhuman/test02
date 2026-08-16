# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-17 00:00:00
"""Rules Admin API 集成测试（APC-T019，需 DB）。

覆盖：
    - RBAC：非 Admin（Viewer）被拒 403；无 token 401。
    - validate：校验规则包 YAML（不入库）。
    - upload：上传新版本（version 递增 + 旧版本自动关闭 + audit 留痕）。
    - activate：激活指定版本（旧版本关闭 + 目标生效 + audit 留痕）。
    - list：列出版本（当前生效 + 历史）。
    - audit：变更写 audit_log（追溯变更人/版本）。

模式（与 test_state_engine 同）：``dependency_overrides[get_principal_dep]`` 注入固定
Principal（Admin/Viewer），真实 ``get_rules_context_dep``（真实 DB）。全程 TestClient，
无外部 asyncio.run DB 访问（避免跨 loop engine 问题）。
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from server.app import db as db_module
from server.app.auth.domain import Principal, Role
from server.app.common.ids import new_id
from server.app.db import get_session_factory
from server.app.main import clear_workers, create_app
from server.app.models.rules import AuditLog
from server.app.models.rules import EvidencePolicy as Orm
from server.app.settings import get_settings

pytestmark = pytest.mark.integration

NOW = datetime(2026, 8, 17, 0, 0, 0, tzinfo=UTC)


async def _cleanup_tables() -> None:
    """清空 evidence_policy（version 递增校验要求测试间无残留）。

    audit_log 为 append-only（§22.2 PG trigger 拒绝 DELETE），不可清；audit 测试用
    唯一 actor 区分自己写入的记录。在 TestClient 启动前单 asyncio.run 执行。
    """
    factory = get_session_factory(get_settings())
    async with factory() as s:
        await s.execute(delete(Orm))
        await s.commit()


VALID_YAML_TEMPLATE = """
policy_type: triage
region: CN
version: {version}
effective_from: 2026-08-17T00:00:00+08:00
source: "test"
rule_text: "r"
display_text: "d"
rules:
  - rule_id: r1
    conditions:
      - op: lt
        field: baby_age_days
        value: 90
    action:
      verdict: warn
      outputs: {{alert_level: yellow}}
      reason_code: r1
      evidence_text: "e"
"""


def _yaml(version: int) -> str:
    return VALID_YAML_TEMPLATE.format(version=version)


@pytest.fixture
def admin_client() -> Iterator[TestClient]:
    """TestClient + 注入 Admin Principal（规则变更权限）。"""
    get_settings.cache_clear()
    db_module.reset_db()
    asyncio.run(_cleanup_tables())
    db_module.reset_db()  # 释放 cleanup loop 的 engine，TestClient 请求时重建绑定其 loop。
    clear_workers()
    app = create_app(get_settings())

    from server.app.di import get_principal_dep

    app.dependency_overrides[get_principal_dep] = lambda: Principal(
        user_id=new_id(), family_id=new_id(), role=Role.ADMIN
    )
    with TestClient(app) as c:
        yield c
    db_module.reset_db()


@pytest.fixture
def viewer_client() -> Iterator[TestClient]:
    """TestClient + 注入 Viewer Principal（无 rule:* 权限，应被拒 403）。"""
    get_settings.cache_clear()
    db_module.reset_db()
    asyncio.run(_cleanup_tables())
    db_module.reset_db()  # 释放 cleanup loop 的 engine，TestClient 请求时重建绑定其 loop。
    clear_workers()
    app = create_app(get_settings())

    from server.app.di import get_principal_dep

    app.dependency_overrides[get_principal_dep] = lambda: Principal(
        user_id=new_id(), family_id=new_id(), role=Role.VIEWER
    )
    with TestClient(app) as c:
        yield c
    db_module.reset_db()


# ---- RBAC ----


def test_validate_without_token_returns_401():
    """无 Authorization header → 401（get_principal_dep 抛 AuthError）。"""
    get_settings.cache_clear()
    db_module.reset_db()
    clear_workers()
    app = create_app(get_settings())
    with TestClient(app) as c:
        resp = c.post("/api/v1/rules/policies:validate", json={"yaml": _yaml(1)})
    assert resp.status_code == 401


def test_validate_viewer_forbidden(viewer_client: TestClient):
    """Viewer 无 rule:configure → 403。"""
    resp = viewer_client.post("/api/v1/rules/policies:validate", json={"yaml": _yaml(1)})
    assert resp.status_code == 403


def test_upload_viewer_forbidden(viewer_client: TestClient):
    """Viewer 无 rule:configure → 403。"""
    resp = viewer_client.post("/api/v1/rules/policies", json={"yaml": _yaml(1)})
    assert resp.status_code == 403


def test_activate_viewer_forbidden(viewer_client: TestClient):
    """Viewer 无 rule:activate → 403。"""
    resp = viewer_client.post(
        "/api/v1/rules/policies:activate",
        json={"policy_type": "triage", "region": "CN", "version": 1},
    )
    assert resp.status_code == 403


# ---- validate ----


def test_validate_ok(admin_client: TestClient):
    """Admin 校验规则包 → 200 + 校验摘要（不入库）。"""
    resp = admin_client.post("/api/v1/rules/policies:validate", json={"yaml": _yaml(1)})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["policy_type"] == "triage"
    assert body["region"] == "CN"
    assert body["version"] == 1
    assert body["rules_count"] == 1
    assert len(body["hash"]) == 64


def test_validate_invalid_yaml_returns_400(admin_client: TestClient):
    """非法 YAML → 400。"""
    resp = admin_client.post(
        "/api/v1/rules/policies:validate", json={"yaml": ": not: valid: yaml:"}
    )
    assert resp.status_code == 400


def test_validate_missing_field_returns_400(admin_client: TestClient):
    """缺必填字段 → 400（Pydantic ValidationError 映射）。"""
    bad = _yaml(1).replace("version: 1\n", "")
    resp = admin_client.post("/api/v1/rules/policies:validate", json={"yaml": bad})
    assert resp.status_code == 400


# ---- upload + activate + list ----


def test_upload_creates_new_version_and_closes_old(admin_client: TestClient):
    """上传 v1 → 上传 v2：v1 自动关闭（effective_to 非 None），v2 当前生效。"""
    r1 = admin_client.post("/api/v1/rules/policies", json={"yaml": _yaml(1)})
    assert r1.status_code == 201, r1.text
    body1 = r1.json()
    assert body1["version"] == 1
    assert body1["is_current"] is True
    assert body1["effective_to"] is None

    r2 = admin_client.post("/api/v1/rules/policies", json={"yaml": _yaml(2)})
    assert r2.status_code == 201, r2.text
    body2 = r2.json()
    assert body2["version"] == 2
    assert body2["is_current"] is True

    # list 验证：v1 已关闭，v2 当前生效。
    lst = admin_client.get("/api/v1/rules/policies?policy_type=triage&region=CN")
    assert lst.status_code == 200, lst.text
    policies = {p["version"]: p for p in lst.json()}
    assert policies[1]["is_current"] is False
    assert policies[1]["effective_to"] is not None
    assert policies[2]["is_current"] is True
    assert policies[2]["effective_to"] is None


def test_upload_non_increasing_version_returns_400(admin_client: TestClient):
    """上传 v1 后再上传 v1（不递增）→ 400。"""
    admin_client.post("/api/v1/rules/policies", json={"yaml": _yaml(1)})
    r = admin_client.post("/api/v1/rules/policies", json={"yaml": _yaml(1)})
    assert r.status_code == 400
    assert "strictly increase" in r.text


def test_activate_reopens_old_version(admin_client: TestClient):
    """上传 v1+v2 → 激活回 v1：v2 关闭，v1 重新生效。"""
    admin_client.post("/api/v1/rules/policies", json={"yaml": _yaml(1)})
    admin_client.post("/api/v1/rules/policies", json={"yaml": _yaml(2)})

    resp = admin_client.post(
        "/api/v1/rules/policies:activate",
        json={"policy_type": "triage", "region": "CN", "version": 1},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["version"] == 1
    assert body["is_current"] is True

    lst = admin_client.get("/api/v1/rules/policies?policy_type=triage&region=CN")
    policies = {p["version"]: p for p in lst.json()}
    assert policies[1]["is_current"] is True
    assert policies[2]["is_current"] is False
    assert policies[2]["effective_to"] is not None


def test_activate_unknown_version_returns_400(admin_client: TestClient):
    """激活不存在版本 → 400。"""
    resp = admin_client.post(
        "/api/v1/rules/policies:activate",
        json={"policy_type": "triage", "region": "CN", "version": 99},
    )
    assert resp.status_code == 400
    assert "not found" in resp.text


def test_list_filters_by_policy_type(admin_client: TestClient):
    """list 按 policy_type 过滤。"""
    admin_client.post(
        "/api/v1/rules/policies", json={"yaml": _yaml(1).replace("triage", "medication")}
    )
    admin_client.post("/api/v1/rules/policies", json={"yaml": _yaml(1)})

    triage = admin_client.get("/api/v1/rules/policies?policy_type=triage")
    assert len(triage.json()) == 1
    assert triage.json()[0]["policy_type"] == "triage"

    med = admin_client.get("/api/v1/rules/policies?policy_type=medication")
    assert len(med.json()) == 1
    assert med.json()[0]["policy_type"] == "medication"


# ---- audit（纯 asyncio.run 模式，避免与 TestClient 跨 loop；与 test_audit 同）----


def _parse_pack_yaml(yaml_text: str):
    """复用 routes._parse_pack 解析 YAML → RulePack。"""
    from server.app.rule_engine.api.routes import _parse_pack

    return _parse_pack(yaml_text)


def test_upload_writes_audit_log():
    """上传规则包 → audit_log 写入（追溯变更人/版本）。

    纯 asyncio.run：直接构造 RulesContext（evidence_repo + audit_service 共享 session），
    模拟路由层 upsert + audit.append + commit，验证 audit_log 落库。
    """
    import asyncio

    from server.app.common.clock import FixedClock
    from server.app.db import get_session_factory
    from server.app.observability.audit import AuditService
    from server.app.rule_engine.evidence_repo import SqlAlchemyEvidencePolicyRepository

    db_module.reset_db()
    actor = (
        new_id()
    )  # 唯一 actor，按此过滤本测试写入的 audit 记录（audit_log append-only 不可清）。

    async def run():
        factory = get_session_factory(get_settings())
        async with factory() as s:
            await s.execute(delete(Orm))
            await s.commit()
        async with factory() as s:
            repo = SqlAlchemyEvidencePolicyRepository(s, clock=FixedClock(NOW))
            audit = AuditService(s, FixedClock(NOW))
            pack = _parse_pack_yaml(_yaml(1))
            await repo.upsert(pack)
            await audit.append(
                actor=actor,
                action="rule.upload",
                resource=f"evidence_policy/{pack.policy_type}/{pack.region}@v{pack.version}",
                after={
                    "policy_type": pack.policy_type,
                    "region": pack.region,
                    "version": pack.version,
                },
                rule_version=f"{pack.policy_type}@{pack.version}",
            )
            await s.commit()
            rows = list(
                (await s.execute(select(AuditLog).where(AuditLog.actor == actor))).scalars().all()
            )
            return rows

    rows = asyncio.run(run())
    assert len(rows) == 1
    assert rows[0].action == "rule.upload"
    assert rows[0].rule_version == "triage@1"
    assert rows[0].actor == actor
    assert "triage/CN@v1" in rows[0].resource


def test_activate_writes_audit_log():
    """激活规则版本 → audit_log 写入。"""
    import asyncio

    from server.app.common.clock import FixedClock
    from server.app.db import get_session_factory
    from server.app.observability.audit import AuditService
    from server.app.rule_engine.evidence_repo import SqlAlchemyEvidencePolicyRepository

    db_module.reset_db()
    actor = (
        new_id()
    )  # 唯一 actor，按此过滤本测试写入的 audit 记录（audit_log append-only 不可清）。

    async def run():
        factory = get_session_factory(get_settings())
        async with factory() as s:
            await s.execute(delete(Orm))
            await s.commit()
        async with factory() as s:
            repo = SqlAlchemyEvidencePolicyRepository(s, clock=FixedClock(NOW))
            audit = AuditService(s, FixedClock(NOW))
            await repo.upsert(_parse_pack_yaml(_yaml(1)))
            await repo.upsert(_parse_pack_yaml(_yaml(2)))
            await repo.activate("triage", "CN", 1)
            await audit.append(
                actor=actor,
                action="rule.activate",
                resource="evidence_policy/triage/CN@v1",
                after={"policy_type": "triage", "region": "CN", "version": 1, "activated": True},
                rule_version="triage@1",
            )
            await s.commit()
            return list(
                (await s.execute(select(AuditLog).where(AuditLog.actor == actor))).scalars().all()
            )

    rows = asyncio.run(run())
    assert len(rows) == 1
    assert rows[0].rule_version == "triage@1"
    assert rows[0].actor == actor

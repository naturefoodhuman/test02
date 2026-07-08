# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 01:15:00


"""APC-T007 Auth/RBAC unit tests."""

from __future__ import annotations

import pytest

from server.app.auth.domain.models import DeviceKind, Principal, Role
from server.app.auth.infra.repository import InMemoryAuthRepository
from server.app.auth.service.auth_service import AuthService, PermissionDenied
from server.app.auth.service.jwt_service import JWTService
from server.app.auth.service.passwords import PasswordHasher


def test_password_hash_does_not_store_plaintext_and_verifies() -> None:
    hasher = PasswordHasher(iterations=10_000)
    encoded = hasher.hash_secret("123456")

    assert "123456" not in encoded
    assert encoded.startswith("pbkdf2_sha256$")
    assert hasher.verify_secret("123456", encoded)
    assert not hasher.verify_secret("bad", encoded)


@pytest.mark.asyncio
async def test_auth_service_creates_family_admin_and_jwt_claims() -> None:
    service = AuthService(
        InMemoryAuthRepository(),
        JWTService("unit-secret-at-least-16"),
        PasswordHasher(iterations=10_000),
    )

    family, admin = await service.create_family_with_admin(
        family_name="Test Family",
        admin_display_name="Dad",
        admin_secret="secret123",
    )
    login = await service.authenticate(
        family_id=family.id,
        display_name="Dad",
        secret="secret123",
        device_id="device-1",
    )
    principal = await service.principal_from_token(login.access_token)

    assert admin.auth_hash is not None
    assert "secret123" not in admin.auth_hash
    assert principal.user_id == admin.id
    assert principal.family_id == family.id
    assert principal.role == Role.ADMIN
    assert principal.device_id == "device-1"


def test_rbac_allows_admin_and_denies_viewer() -> None:
    service = AuthService(InMemoryAuthRepository(), JWTService("unit-secret-at-least-16"))

    service.require_roles(
        Principal(user_id="u", family_id="f", role=Role.ADMIN),
        {Role.ADMIN},
    )
    with pytest.raises(PermissionDenied):
        service.require_roles(
            Principal(user_id="u", family_id="f", role=Role.VIEWER),
            {Role.ADMIN},
        )


@pytest.mark.asyncio
async def test_register_device_requires_allowed_role() -> None:
    repo = InMemoryAuthRepository()
    service = AuthService(repo, JWTService("unit-secret-at-least-16"))

    device = await service.register_device(
        principal=Principal(user_id="u", family_id="f", role=Role.ADMIN),
        kind=DeviceKind.PHONE,
        name="Dad phone",
        fcm_token="fake-token",
    )

    assert device.kind == DeviceKind.PHONE
    assert device.fcm_token == "fake-token"
    assert repo.devices[device.id] == device

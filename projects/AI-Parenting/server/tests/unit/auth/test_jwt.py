# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""JWT 签发/解析单元测试（APC-T007 测试要求：Unit JWT 签发/解析）。

验证 ``Hs256JwtService``：
    - issue/parse 往返：claims 完整还原（user_id/family_id/role/device_id + iat/exp/jti）。
    - 篡改签名 → TokenInvalidError。
    - 篡改 payload → TokenInvalidError（签名不匹配）。
    - 过期 → TokenExpiredError。
    - alg=none 伪造 → TokenInvalidError（防降级攻击）。
    - 格式错（非三段）→ TokenMalformedError。
    - 缺密钥 → AuthConfigError（fail-fast）。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from server.app.auth.domain import Role, TokenClaims
from server.app.auth.service.jwt import (
    AuthConfigError,
    Hs256JwtService,
    TokenExpiredError,
    TokenInvalidError,
    TokenMalformedError,
)
from server.app.common.errors import AuthError

_SECRET = "test-secret-key-not-for-prod"


def _make_claims(
    *,
    role: Role = Role.ADMIN,
    device_id: str | None = "01JZDEVICE",
    exp_delta: timedelta = timedelta(hours=1),
) -> TokenClaims:
    # iat 用真实 now，避免 parse 时因系统时钟已过固定时刻而过期（flaky）。
    now = datetime.now(tz=UTC)
    return TokenClaims(
        user_id="01JZUSER0001",
        family_id="01JZFAMILY01",
        role=role,
        device_id=device_id,
        iat=now,
        exp=now + exp_delta,
        jti="01JZJTI000000000000001",
    )


def _service(secret: str = _SECRET, ttl: int = 3600) -> Hs256JwtService:
    return Hs256JwtService(secret=secret, access_ttl_seconds=ttl)


def test_issue_and_parse_roundtrip():
    svc = _service()
    claims = _make_claims()
    token = svc.issue(claims)
    assert token.count(".") == 2  # header.payload.signature

    parsed = svc.parse(token)
    assert parsed.user_id == claims.user_id
    assert parsed.family_id == claims.family_id
    assert parsed.role == claims.role
    assert parsed.device_id == claims.device_id
    assert parsed.jti == claims.jti
    # iat/exp 经 epoch 秒往返（秒精度，微秒被截断），比对 epoch 秒相等即可。
    assert int(parsed.iat.timestamp()) == int(claims.iat.timestamp())
    assert int(parsed.exp.timestamp()) == int(claims.exp.timestamp())


def test_parse_device_id_none_preserved():
    svc = _service()
    claims = _make_claims(device_id=None)
    token = svc.issue(claims)
    parsed = svc.parse(token)
    assert parsed.device_id is None


def test_parse_tampered_signature_raises_invalid():
    svc = _service()
    token = svc.issue(_make_claims())
    header, payload, _sig = token.split(".")
    # 用错误密钥重签 signature 段。
    other = Hs256JwtService(secret="different-secret", access_ttl_seconds=3600)
    forged_sig = other.issue(_make_claims()).split(".")[2]
    tampered = f"{header}.{payload}.{forged_sig}"
    with pytest.raises(TokenInvalidError):
        svc.parse(tampered)


def test_parse_tampered_payload_raises_invalid():
    """篡改 payload（如改 role）→ 签名不匹配 → TokenInvalidError。"""
    import base64
    import json

    svc = _service()
    token = svc.issue(_make_claims(role=Role.ADMIN))
    header, payload, sig = token.split(".")
    # 解 payload、改 role、重编码（签名不变 → 不匹配）。
    raw = json.loads(base64.urlsafe_b64decode(payload + "=="))
    raw["role"] = "viewer"
    new_payload = (
        base64.urlsafe_b64encode(json.dumps(raw, separators=(",", ":")).encode())
        .rstrip(b"=")
        .decode()
    )
    tampered = f"{header}.{new_payload}.{sig}"
    with pytest.raises((TokenInvalidError, TokenMalformedError)):
        svc.parse(tampered)


def test_parse_expired_token_raises_expired():
    svc = _service()
    # exp 远在过去（确保任何真实 now 都已过期）。
    claims = _make_claims(exp_delta=timedelta(days=-365))
    token = svc.issue(claims)
    with pytest.raises(TokenExpiredError):
        svc.parse(token)


def test_parse_alg_none_forgery_raises_invalid():
    """防 alg=none 降级攻击：header alg=none 应被拒。"""
    import base64
    import json

    svc = _service()
    # 构造 alg=none 的 header + 空 signature。
    header = (
        base64.urlsafe_b64encode(
            json.dumps({"alg": "none", "typ": "JWT"}, separators=(",", ":")).encode()
        )
        .rstrip(b"=")
        .decode()
    )
    payload = (
        base64.urlsafe_b64encode(
            json.dumps(
                {
                    "user_id": "01JZUSER",
                    "family_id": "01JZFAM",
                    "role": "admin",
                    "device_id": None,
                    "iat": 1723377600,
                    "exp": 9999999999,
                    "jti": "x",
                },
                separators=(",", ":"),
            ).encode()
        )
        .rstrip(b"=")
        .decode()
    )
    forged = f"{header}.{payload}."
    with pytest.raises(TokenInvalidError):
        svc.parse(forged)


def test_parse_malformed_token_raises_malformed():
    svc = _service()
    with pytest.raises(TokenMalformedError):
        svc.parse("not.a.jwt.token")  # 四段
    with pytest.raises(TokenMalformedError):
        svc.parse("onlyonepart")
    with pytest.raises(TokenMalformedError):
        svc.parse("a.b")  # 两段


def test_missing_secret_raises_config_error():
    """缺密钥 fail-fast（§8.3）：空字符串 → AuthConfigError。"""
    with pytest.raises(AuthConfigError):
        Hs256JwtService(secret="", access_ttl_seconds=3600)


def test_jwt_errors_are_auth_error_subclasses():
    """所有 token 错误是 AuthError 子类（网关层统一映射 401）。"""
    assert issubclass(TokenMalformedError, AuthError)
    assert issubclass(TokenInvalidError, AuthError)
    assert issubclass(TokenExpiredError, AuthError)
    assert issubclass(AuthConfigError, AuthError)
    # http_status 应为 401（AuthError 默认）。
    assert TokenMalformedError("x").http_status == 401
    assert TokenExpiredError("x").http_status == 401

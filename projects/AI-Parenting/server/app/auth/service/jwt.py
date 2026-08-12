# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/auth/service/jwt.py —— JWT 签发/解析服务（HS256，标准库实现）。
# 依据：ENGINEERING_DESIGN §2（M02 auth）、§9.1（AuthError 401/403）、§20（安全：令牌鉴权）；
#       ARCHITECTURE_FINAL §19（权限）、§15.2（Auth 域 /login /refresh）；TASK_BACKLOG APC-T007。
# 设计：HS256（RFC 7519 + RFC 7515），标准库 hmac/hashlib/base64/json，不引入 PyJWT（最小依赖）。
#       claims SSOT：user_id/family_id/role/device_id + 标准 iat/exp/jti（与 domain.TokenClaims 对齐）。
#       密钥来自 Settings.auth.jwt_secret（§8.3 密钥管理：.env / _infra/.env，gitignored）。
#       解析失败（签名错/过期/格式错）→ AuthError 子类（401，细分 code 便于审计/日志）。
# 边界：只做签发/解析，不做用户查找/权限判定（在 AuthService）；不缓存令牌。

"""JWT 签发/解析服务（HS256，标准库实现）。

架构（§20 安全：令牌鉴权）：局域网内 TLS + 令牌。本实现用 HS256（对称签名），
标准库 ``hmac`` / ``hashlib`` / ``base64`` / ``json``，不引入 ``PyJWT``（最小依赖原则）。

claims SSOT（TASK_BACKLOG APC-T007）：``user_id`` / ``family_id`` / ``role`` / ``device_id``
+ 标准 ``iat`` / ``exp`` / ``jti``（与 ``domain.TokenClaims`` 一一对应）。

密钥来自 ``Settings.auth.jwt_secret``（§8.3：``.env`` / ``_infra/.env``，gitignored）。
解析失败（签名错误 / 过期 / 格式错误 / claims 缺失）抛 ``AuthError`` 子类（401），
细分 ``code`` 便于审计与日志排障（§22.2）。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime

from ...common.clock import Clock, SystemClock
from ...common.errors import AuthError
from ...common.ids import new_id
from ..domain import Role, TokenClaims

_ALGORITHM = "HS256"
_HEADER = {"alg": _ALGORITHM, "typ": "JWT"}


# ---- AuthError 细分子类（§9.1：AuthError 401；细分 code 便于审计/日志）----
# 放本模块而非 common/errors.py：JWT 解析细节是 auth 内部关注点，网关层只看 AuthError→401。


class TokenMalformedError(AuthError):
    """令牌格式错误（非三段 / base64 解码失败 / payload 非 JSON）。"""

    code = "PARENTING.AUTH.TOKEN_MALFORMED"


class TokenInvalidError(AuthError):
    """令牌无效（签名错 / header alg 不符 / claims 缺失或非法）。"""

    code = "PARENTING.AUTH.TOKEN_INVALID"


class TokenExpiredError(AuthError):
    """令牌已过期（exp 已过）。"""

    code = "PARENTING.AUTH.TOKEN_EXPIRED"


class AuthConfigError(AuthError):
    """认证配置错误（如 JWT 密钥缺失）—— fail-fast，启动即暴露。"""

    code = "PARENTING.AUTH.CONFIG"


def _b64url_encode(data: bytes) -> str:
    """base64url 编码（无 padding，RFC 7515 §2）。"""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(segment: str) -> bytes:
    """base64url 解码；自动补 padding，格式错抛 ValueError（调用方映射为 TokenMalformedError）。"""
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def _sign(signing_input: bytes, secret: str) -> bytes:
    """HMAC-SHA256 签名。"""
    return hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()


def _to_epoch(dt: datetime) -> int:
    """datetime → epoch 秒（UTC）。naive 视为 UTC（防御性，正常不应传入 naive）。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return int(dt.timestamp())


def _from_epoch(seconds: int) -> datetime:
    """epoch 秒 → timezone-aware datetime（UTC）。"""
    return datetime.fromtimestamp(seconds, tz=UTC)


class Hs256JwtService:
    """HS256 JWT 签发/解析服务（实现 ``domain.JwtService``）。

    生命周期：进程级单例（无状态，仅依赖密钥与 TTL，可安全复用）。
    """

    def __init__(
        self,
        *,
        secret: str,
        access_ttl_seconds: int,
        clock: Clock | None = None,
    ) -> None:
        if not secret:
            # 密钥缺失是部署错误，fail-fast 暴露（§8.3）。
            raise AuthConfigError("JWT secret is not configured")
        self._secret = secret
        self._access_ttl_seconds = access_ttl_seconds
        # 过期校验用注入时钟（与 issue 对称：签发用 AuthService 的 Clock，
        # 解析用本 Clock）。默认 SystemClock；测试注入 FixedClock 控制时间，
        # 避免 wall clock 跨天后 FixedClock 签发的 token 误判过期。
        self._clock: Clock = clock or SystemClock()

    def issue(self, claims: TokenClaims) -> str:
        """签发 JWT 字符串（含签名）。"""
        header_b64 = _b64url_encode(json.dumps(_HEADER, separators=(",", ":")).encode("utf-8"))
        payload = {
            "user_id": claims.user_id,
            "family_id": claims.family_id,
            "role": claims.role.value,
            "device_id": claims.device_id,
            "iat": _to_epoch(claims.iat),
            "exp": _to_epoch(claims.exp),
            "jti": claims.jti,
        }
        payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        signature = _sign(signing_input, self._secret)
        signature_b64 = _b64url_encode(signature)
        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def parse(self, token: str) -> TokenClaims:
        """解析并校验 JWT；失败抛 ``AuthError`` 子类（401）。

        校验项：格式（三段）、header alg、签名（常量时间）、exp 过期、claims 完整性。
        """
        parts = token.split(".")
        if len(parts) != 3:
            raise TokenMalformedError("Malformed token")
        header_b64, payload_b64, signature_b64 = parts

        # header 校验（防 alg=none 伪造）。
        try:
            header = json.loads(_b64url_decode(header_b64))
        except (ValueError, json.JSONDecodeError) as exc:
            raise TokenMalformedError("Malformed token header") from exc
        if header.get("alg") != _ALGORITHM or header.get("typ") != "JWT":
            raise TokenInvalidError("Unsupported token header")

        # 签名校验（常量时间，防时序侧信道）。
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = _sign(signing_input, self._secret)
        try:
            actual_sig = _b64url_decode(signature_b64)
        except ValueError as exc:
            raise TokenMalformedError("Malformed token signature") from exc
        if not hmac.compare_digest(expected_sig, actual_sig):
            raise TokenInvalidError("Invalid token signature")

        # payload 解析。
        try:
            payload = json.loads(_b64url_decode(payload_b64))
        except (ValueError, json.JSONDecodeError) as exc:
            raise TokenMalformedError("Malformed token payload") from exc

        # exp 过期校验。
        exp_raw = payload.get("exp")
        if not isinstance(exp_raw, int):
            raise TokenInvalidError("Missing exp claim")
        exp = _from_epoch(exp_raw)
        if self._clock.now() >= exp:
            raise TokenExpiredError("Token expired")

        # claims 完整性（SSOT：user_id/family_id/role/device_id）。
        try:
            role = Role(payload["role"])
            user_id = payload["user_id"]
            family_id = payload["family_id"]
        except (KeyError, ValueError) as exc:
            raise TokenInvalidError("Invalid token claims") from exc
        device_id = payload.get("device_id")

        iat_raw = payload.get("iat")
        iat = _from_epoch(iat_raw) if isinstance(iat_raw, int) else exp
        jti = payload.get("jti") or new_id()

        return TokenClaims(
            user_id=user_id,
            family_id=family_id,
            role=role,
            device_id=device_id,
            iat=iat,
            exp=exp,
            jti=jti,
        )


__all__ = [
    "AuthConfigError",
    "Hs256JwtService",
    "TokenExpiredError",
    "TokenInvalidError",
    "TokenMalformedError",
]

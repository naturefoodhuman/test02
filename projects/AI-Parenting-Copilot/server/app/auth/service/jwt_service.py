# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 01:15:00


"""Small HS256 JWT service without external network or SaaS dependency."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

from server.app.common.clock import utc_now
from server.app.common.errors import AppError


class TokenError(AppError):
    status_code = 401
    code = "TOKEN_INVALID"


@dataclass(frozen=True)
class TokenClaims:
    user_id: str
    family_id: str
    role: str
    device_id: str | None
    exp: int
    iat: int


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


class JWTService:
    """HS256 JWT issuer/parser for local API authentication."""

    def __init__(self, secret: str, *, ttl_seconds: int = 86_400) -> None:
        if not secret or len(secret) < 16:
            raise ValueError("jwt secret must be at least 16 characters")
        self.secret = secret.encode()
        self.ttl_seconds = ttl_seconds

    def issue(
        self,
        *,
        user_id: str,
        family_id: str,
        role: str,
        device_id: str | None = None,
    ) -> str:
        now = int(utc_now().timestamp())
        payload = {
            "user_id": user_id,
            "family_id": family_id,
            "role": role,
            "device_id": device_id,
            "iat": now,
            "exp": now + self.ttl_seconds,
        }
        return self._encode(payload)

    def parse(self, token: str) -> TokenClaims:
        try:
            header_b64, payload_b64, signature_b64 = token.split(".", 2)
            signing_input = f"{header_b64}.{payload_b64}".encode()
            expected = _b64url(hmac.new(self.secret, signing_input, hashlib.sha256).digest())
            if not hmac.compare_digest(signature_b64, expected):
                raise TokenError("Token signature mismatch")
            payload = json.loads(_b64url_decode(payload_b64))
        except AppError:
            raise
        except Exception as exc:
            raise TokenError("Token is malformed") from exc
        exp = int(payload.get("exp", 0))
        if exp < int(utc_now().timestamp()):
            raise TokenError("Token expired")
        return TokenClaims(
            user_id=str(payload["user_id"]),
            family_id=str(payload["family_id"]),
            role=str(payload["role"]),
            device_id=payload.get("device_id"),
            exp=exp,
            iat=int(payload["iat"]),
        )

    def _encode(self, payload: dict[str, Any]) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode())
        payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode())
        signing_input = f"{header_b64}.{payload_b64}".encode()
        signature = _b64url(hmac.new(self.secret, signing_input, hashlib.sha256).digest())
        return f"{header_b64}.{payload_b64}.{signature}"

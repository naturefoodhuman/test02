# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
#
# app/auth/service/password.py —— 密码/PIN 哈希服务（PBKDF2-HMAC-SHA256）。
# 依据：ENGINEERING_DESIGN §9.1（AuthError）、§20（安全：不得明文存储）；
#       ARCHITECTURE_FINAL §19/§20；TASK_BACKLOG APC-T007（密码或 PIN hash 不得明文存储）。
# 设计：标准库 hashlib.pbkdf2_hmac（sha256，高迭代），随机 salt，base64 存储。
#       不引入 passlib/argon2/bcrypt（最小依赖原则；pyproject 未声明）。
#       存储格式自洽：``pbkdf2_sha256$<iterations>$<salt_b64>$<digest_b64>``，verify 解析回放。
#       常量时间比较（hmac.compare_digest）防时序侧信道。
# 边界：只做哈希/校验，不做用户查找/角色判定（在 AuthService）。

"""密码/PIN 哈希服务（PBKDF2-HMAC-SHA256）。

架构（§20 安全）：密码或 PIN 不得明文存储。本实现用标准库 ``hashlib.pbkdf2_hmac``
（sha256），每条凭证独立随机 salt，存储为自洽格式串：

    ``pbkdf2_sha256$<iterations>$<salt_b64>$<digest_b64>``

不引入 ``passlib`` / ``argon2`` / ``bcrypt``（最小依赖原则；pyproject 未声明）。
``verify`` 用 ``hmac.compare_digest`` 做常量时间比较，防时序侧信道。
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import os

# 迭代次数：NIST SP 800-132 建议 ≥ 10000；取 310000 与 OWASP 2023 推荐量级对齐。
# 单次哈希耗时约数十毫秒，局域网家庭场景登录频率低，可接受。
_DEFAULT_ITERATIONS = 310_000
# salt 长度 16 字节（128 位），NIST SP 800-132 建议至少 128 位。
_SALT_BYTES = 16
# digest 长度 32 字节（sha256 输出）。
_DIGEST_BYTES = 32
_ALGORITHM = "pbkdf2_sha256"


class Pbkdf2PasswordHasher:
    """PBKDF2-HMAC-SHA256 密码哈希器（实现 ``domain.PasswordHasher``）。"""

    def __init__(self, *, iterations: int = _DEFAULT_ITERATIONS) -> None:
        self._iterations = iterations

    def hash(self, plain: str) -> str:
        """对明文生成可存储的哈希串（含算法/迭代/salt/digest）。

        每次调用生成新随机 salt，故同一明文哈希结果不同（防彩虹表/重放）。
        """
        salt = os.urandom(_SALT_BYTES)
        digest = hashlib.pbkdf2_hmac(
            "sha256", plain.encode("utf-8"), salt, self._iterations, dklen=_DIGEST_BYTES
        )
        return self._encode(self._iterations, salt, digest)

    def verify(self, plain: str, stored: str) -> bool:
        """校验明文与存储哈希是否匹配（常量时间比较）。

        格式不符或算法不匹配返回 ``False``（不抛异常，由调用方映射为 ``AuthError``）。
        """
        parsed = self._decode(stored)
        if parsed is None:
            return False
        algorithm, iterations, salt, expected = parsed
        if algorithm != _ALGORITHM:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", plain.encode("utf-8"), salt, iterations, dklen=len(expected)
        )
        return hmac.compare_digest(actual, expected)

    @staticmethod
    def _encode(iterations: int, salt: bytes, digest: bytes) -> str:
        return (
            f"{_ALGORITHM}${iterations}$"
            f"{base64.b64encode(salt).decode('ascii')}$"
            f"{base64.b64encode(digest).decode('ascii')}"
        )

    @staticmethod
    def _decode(stored: str) -> tuple[str, int, bytes, bytes] | None:
        """解析存储串；格式不符返回 None。"""
        parts = stored.split("$")
        if len(parts) != 4:
            return None
        algorithm, iterations_str, salt_b64, digest_b64 = parts
        try:
            iterations = int(iterations_str)
            salt = base64.b64decode(salt_b64)
            digest = base64.b64decode(digest_b64)
        except (ValueError, binascii.Error):
            return None
        return algorithm, iterations, salt, digest


__all__ = ["Pbkdf2PasswordHasher"]

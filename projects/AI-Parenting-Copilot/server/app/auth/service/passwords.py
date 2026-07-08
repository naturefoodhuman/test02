# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 01:15:00


"""Password/PIN hashing using stdlib PBKDF2-HMAC-SHA256."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os


class PasswordHasher:
    """PBKDF2 password hasher.

    The output format is: `pbkdf2_sha256$iterations$salt_b64$digest_b64`.
    """

    algorithm = "pbkdf2_sha256"

    def __init__(self, *, iterations: int = 210_000, salt_bytes: int = 16) -> None:
        self.iterations = iterations
        self.salt_bytes = salt_bytes

    def hash_secret(self, secret: str) -> str:
        if not secret:
            raise ValueError("secret must not be empty")
        salt = os.urandom(self.salt_bytes)
        digest = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt, self.iterations)
        return "$".join(
            [
                self.algorithm,
                str(self.iterations),
                base64.urlsafe_b64encode(salt).decode(),
                base64.urlsafe_b64encode(digest).decode(),
            ]
        )

    def verify_secret(self, secret: str, encoded: str) -> bool:
        try:
            algorithm, raw_iterations, raw_salt, raw_digest = encoded.split("$", 3)
            if algorithm != self.algorithm:
                return False
            iterations = int(raw_iterations)
            salt = base64.urlsafe_b64decode(raw_salt.encode())
            expected = base64.urlsafe_b64decode(raw_digest.encode())
        except Exception:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt, iterations)
        return hmac.compare_digest(actual, expected)

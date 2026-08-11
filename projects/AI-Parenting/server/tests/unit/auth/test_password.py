# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-11 00:00:00
"""密码哈希单元测试（APC-T007 测试要求：Unit 密码校验）。

验证 ``Pbkdf2PasswordHasher``：
    - 正确密码 verify=True；错误密码 verify=False。
    - 同一明文每次哈希结果不同（随机 salt，防彩虹表）。
    - 格式错/算法不匹配 verify=False（不抛异常）。
    - 常量时间比较（hmac.compare_digest）—— 不直接测时序，验证行为正确。
    - 不得明文存储（§20）：存储串不含明文。
"""

from __future__ import annotations

import pytest

from server.app.auth.service.password import Pbkdf2PasswordHasher


def test_hash_and_verify_correct_password():
    hasher = Pbkdf2PasswordHasher(iterations=10_000)
    stored = hasher.hash("s3cret-PIN")
    assert stored != "s3cret-PIN"  # 不得明文存储（§20）
    assert "s3cret-PIN" not in stored
    assert hasher.verify("s3cret-PIN", stored) is True


def test_verify_wrong_password_returns_false():
    hasher = Pbkdf2PasswordHasher(iterations=10_000)
    stored = hasher.hash("correct-horse")
    assert hasher.verify("wrong", stored) is False


def test_same_plaintext_yields_different_hashes():
    """随机 salt：同一明文两次哈希结果不同（防彩虹表/重放）。"""
    hasher = Pbkdf2PasswordHasher(iterations=10_000)
    h1 = hasher.hash("same-secret")
    h2 = hasher.hash("same-secret")
    assert h1 != h2
    # 但两者都能验证同一明文。
    assert hasher.verify("same-secret", h1) is True
    assert hasher.verify("same-secret", h2) is True


def test_verify_malformed_stored_returns_false():
    hasher = Pbkdf2PasswordHasher(iterations=10_000)
    assert hasher.verify("any", "not-a-valid-format") is False
    assert hasher.verify("any", "pbkdf2_sha256$abc$not$b64") is False
    assert hasher.verify("any", "") is False


def test_verify_unsupported_algorithm_returns_false():
    """算法不匹配（如存储为 argon2）返回 False，不抛异常。"""
    hasher = Pbkdf2PasswordHasher(iterations=10_000)
    # 伪造一个 alg=argon2 的存储串。
    import base64

    fake = (
        f"argon2$10000${base64.b64encode(b'salt').decode()}${base64.b64encode(b'digest').decode()}"
    )
    assert hasher.verify("any", fake) is False


def test_hash_format_contains_algorithm_and_iterations():
    """存储串自洽：含算法标识与迭代次数（便于未来升级算法/参数）。"""
    hasher = Pbkdf2PasswordHasher(iterations=50_000)
    stored = hasher.hash("x")
    assert stored.startswith("pbkdf2_sha256$50000$")
    parts = stored.split("$")
    assert len(parts) == 4


@pytest.mark.parametrize("plain", ["", "a", "中文密码", "p@ss w0rd!"])
def test_verify_various_passwords(plain: str):
    hasher = Pbkdf2PasswordHasher(iterations=10_000)
    stored = hasher.hash(plain)
    assert hasher.verify(plain, stored) is True
    assert hasher.verify(plain + "x", stored) is False

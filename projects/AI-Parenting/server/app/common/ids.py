# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
#
# common/ids.py —— 统一 ID 生成（ULID）。
# 依据：TASK_BACKLOG APC-T002（ID 使用 ULID）；ENGINEERING_DESIGN §5（核心抽象）。
# 设计：ULID 26 字符 Crockford base32，时间有序，适合作为 event_id/baby_id 等主键。
# 复用社区库 python-ulid（pyproject 已声明），不自造实现。

"""统一 ID 生成。

所有领域实体主键统一使用 ULID（26 字符 Crockford base32，时间有序）。
复用社区库 `python-ulid`，不自造实现（社区最佳实践原则）。
"""

from __future__ import annotations

import re

import ulid as _ulid

# ULID 规范：26 字符，Crockford base32，首字符在 [0-7]。
# 与 python-ulid 内部 pattern 一致（见 ulid/__init__.py __get_pydantic_core_schema__）。
ULID_RE = re.compile(r"^[0-7][0-9A-HJKMNP-TV-Z]{25}$")


def new_id() -> str:
    """生成一个新的 ULID 字符串（26 字符，时间有序）。

    线程安全（python-ulid 内部加锁），同一毫秒内单调递增（StrictMonotonicPolicy）。
    """
    return str(_ulid.ULID())


def is_valid_ulid(value: str) -> bool:
    """校验字符串是否为合法 ULID 格式（仅格式校验，不保证存在）。"""
    return bool(ULID_RE.match(value))


def parse_ulid(value: str) -> _ulid.ULID:
    """将 ULID 字符串解析为 ULID 对象（用于提取时间戳等）。

    Raises:
        ValueError: 字符串不是合法 ULID。
    """
    return _ulid.ULID.from_str(value)


__all__ = ["ULID_RE", "is_valid_ulid", "new_id", "parse_ulid"]

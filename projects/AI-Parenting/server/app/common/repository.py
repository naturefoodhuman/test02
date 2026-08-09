# 创建/修改该文件的LLM大模型：Claude Opus 4.8
# 创建时间（北京时间）：2026-08-07 20:15:20
#
# common/repository.py —— Repository 协议（数据访问抽象）。
# 依据：ENGINEERING_DESIGN §5.2（Repository Protocol）；ARCHITECTURE_FINAL §6（数据架构）。
# 设计：以 Protocol + Generic[T] 实现，测试可注入替身。
#       生命周期：请求作用域（FastAPI Depends）；事务边界在 service 层。
#       扩展：新实体 → 新 Repository，不改内核。

"""Repository 协议（数据访问抽象）。

以 ``Protocol`` + ``Generic[T]`` 实现（PEP 544），测试可注入替身。
生命周期：请求作用域（FastAPI ``Depends``）；事务边界在 service 层。
扩展：新实体 → 新 ``Repository``，不改内核（开闭原则）。
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class Repository(Protocol[T]):
    """通用数据访问协议。

    具体实体 Repository 各自实现本协议；本协议只约束 get/upsert/query 三件套，
    不约束具体表/列，避免过早抽象（社区最小接口原则）。
    """

    async def get(self, id_: str) -> T | None:
        """按主键取实体；不存在返回 None。"""
        ...

    async def upsert(self, entity: T) -> T:
        """插入或更新实体；返回落库后的实体（含生成字段）。"""
        ...

    async def query(self, **filters: object) -> list[T]:
        """按过滤条件查询实体列表；无匹配返回空列表。"""
        ...


__all__ = ["Repository", "T"]

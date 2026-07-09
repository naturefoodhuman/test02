# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-08 22:55:00


"""Repository protocol definitions used by bounded contexts."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypeVar

EntityT = TypeVar("EntityT")
IdT = TypeVar("IdT", bound=str, contravariant=True)


class Repository(Protocol[EntityT, IdT]):
    """Minimal async repository contract.

    Concrete SQLAlchemy repositories are introduced after the database schema tasks.
    """

    async def get(self, entity_id: IdT) -> EntityT | None:
        """Return an entity by ID or None."""

    async def add(self, entity: EntityT) -> EntityT:
        """Persist a new entity and return it."""

    async def list(self, *, limit: int = 100, offset: int = 0) -> Sequence[EntityT]:
        """List entities with deterministic pagination."""

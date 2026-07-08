# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-08 22:55:00


"""Dependency injection container and worker registration hooks."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from server.app.settings import Settings, get_settings


class AsyncWorker(Protocol):
    """Lifecycle protocol for future background workers."""

    name: str

    async def start(self) -> None:
        """Start the worker."""

    async def stop(self) -> None:
        """Stop the worker."""


@dataclass
class WorkerRegistry:
    """Registry reserved by APC-T002; no business workers are registered yet."""

    workers: list[AsyncWorker] = field(default_factory=list)

    def register(self, worker: AsyncWorker) -> None:
        """Register a worker for FastAPI lifespan management."""

        self.workers.append(worker)

    async def start_all(self) -> None:
        """Start all registered workers in registration order."""

        for worker in self.workers:
            await worker.start()

    async def stop_all(self) -> None:
        """Stop all registered workers in reverse registration order."""

        for worker in reversed(self.workers):
            await worker.stop()


@dataclass
class AppContainer:
    """Application dependencies exposed through FastAPI app.state."""

    settings: Settings
    worker_registry: WorkerRegistry = field(default_factory=WorkerRegistry)


def create_container(settings: Settings | None = None) -> AppContainer:
    """Create the application dependency container."""

    return AppContainer(settings=settings or get_settings())


def get_container() -> AppContainer:
    """FastAPI dependency placeholder.

    Route-level dependencies may override this in tests once routers are added.
    """

    return create_container()

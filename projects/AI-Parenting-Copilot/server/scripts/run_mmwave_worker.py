# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 18:25:00

"""Run the live mmWave MQTT ingestion worker."""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.app.db import create_engine, create_session_factory  # noqa: E402
from server.app.mmwave.worker import MMWaveMQTTWorker, MMWaveMQTTWorkerConfig  # noqa: E402
from server.app.settings import Settings  # noqa: E402


async def main() -> None:
    settings = Settings()
    if not settings.database.url:
        raise SystemExit("PARENTING_DATABASE__URL is required for live mmWave worker")
    engine = create_engine(settings.database)
    worker = MMWaveMQTTWorker(
        config=MMWaveMQTTWorkerConfig(
            host=settings.mqtt.host,
            port=settings.mqtt.port,
            topics=["baby/radar/telemetry"],
            baby_id=os.getenv("PARENTING_MMWAVE_BABY_ID"),
            family_id=os.getenv("PARENTING_MMWAVE_FAMILY_ID"),
        ),
        session_factory=create_session_factory(engine),
    )
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)
    await worker.start()
    try:
        await stop_event.wait()
    finally:
        await worker.stop()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

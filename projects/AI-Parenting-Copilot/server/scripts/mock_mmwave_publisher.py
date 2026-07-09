# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 10:10:00


"""Mock mmWave publisher for dev and tests.

Dry-run by default: prints fixture frames. Use --mqtt after aiomqtt/Mosquitto are
available to publish to the configured broker.
"""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path


async def publish_mqtt(host: str, port: int, topic: str, frames: list[str]) -> None:
    import aiomqtt

    async with aiomqtt.Client(hostname=host, port=port) as client:
        for frame in frames:
            await client.publish(topic, frame)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="tests/fixtures/radar_frames.jsonl")
    parser.add_argument("--topic", default="baby/radar/telemetry")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--mqtt", action="store_true")
    args = parser.parse_args()
    frames = [line for line in Path(args.fixture).read_text().splitlines() if line.strip()]
    if args.mqtt:
        asyncio.run(publish_mqtt(args.host, args.port, args.topic, frames))
    else:
        for frame in frames:
            print(frame)


if __name__ == "__main__":
    main()

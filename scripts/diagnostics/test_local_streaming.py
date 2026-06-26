#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-26 00:00:00

"""
Local streaming diagnostics for FORGE Claude Code proxy.

Checks two paths:
1. Direct OpenAI-compatible backend streaming (default: http://127.0.0.1:8080/v1/chat/completions)
2. Anthropic-compatible Smart Proxy streaming (default: http://127.0.0.1:4000/v1/messages)

Purpose:
- Determine whether the MTPLX backend is truly token-streaming or returning full JSON.
- Determine whether the Smart Proxy emits Anthropic `content_block_delta` events.
- Measure time to first text delta and total duration.

Run on the user's Mac after `bash scripts/forge-start.sh`:
  python3 scripts/diagnostics/test_local_streaming.py
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class StreamMetric:
    name: str
    status: str
    http_status: int | None = None
    first_delta_s: float | None = None
    total_s: float = 0.0
    delta_count: int = 0
    text_preview: str = ""
    notes: str = ""


def _now() -> float:
    return time.perf_counter()


def test_openai_backend(base_url: str, model: str, prompt: str, timeout: float) -> StreamMetric:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 64,
        "temperature": 0.0,
        "stream": True,
    }
    t0 = _now()
    chunks: list[str] = []
    delta_count = 0
    first_delta = None
    raw_non_sse = []
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout, read=timeout)) as client:
            with client.stream("POST", url, json=payload) as resp:
                status = resp.status_code
                if status != 200:
                    body = resp.read().decode("utf-8", errors="ignore")[:500]
                    return StreamMetric("openai-backend", "http_error", status, total_s=_now() - t0, notes=body)
                for line in resp.iter_lines():
                    if line:
                        raw_non_sse.append(line)
                    if not line or not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        data = json.loads(raw)
                    except Exception:
                        continue
                    for choice in data.get("choices", []):
                        delta = choice.get("delta", {}) or {}
                        text = delta.get("content")
                        if text:
                            delta_count += 1
                            if first_delta is None:
                                first_delta = _now() - t0
                            chunks.append(str(text))
        total = _now() - t0
        if delta_count > 1:
            status_text = "true_streaming"
            notes = "Backend emitted multiple OpenAI SSE delta chunks."
        elif delta_count == 1:
            status_text = "single_delta"
            notes = "Backend emitted one text delta; may be pseudo-streaming."
        else:
            joined = "\n".join(raw_non_sse).strip()
            if joined.startswith("{"):
                status_text = "full_json_not_sse"
                notes = "Backend returned full JSON even though stream=true. Smart Proxy must wrap it."
            else:
                status_text = "empty_stream"
                notes = "No text delta detected."
        return StreamMetric(
            "openai-backend",
            status_text,
            200,
            first_delta,
            total,
            delta_count,
            "".join(chunks)[:120],
            notes,
        )
    except Exception as exc:
        return StreamMetric("openai-backend", "exception", total_s=_now() - t0, notes=repr(exc))


def test_anthropic_proxy(base_url: str, model: str, prompt: str, timeout: float) -> StreamMetric:
    url = base_url.rstrip("/") + "/v1/messages"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 64,
        "stream": True,
    }
    headers = {
        "content-type": "application/json",
        "x-api-key": "sk-forge-local-anytoken",
        "anthropic-version": "2023-06-01",
    }
    t0 = _now()
    chunks: list[str] = []
    delta_count = 0
    first_delta = None
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout, read=timeout)) as client:
            with client.stream("POST", url, headers=headers, json=payload) as resp:
                status = resp.status_code
                if status != 200:
                    body = resp.read().decode("utf-8", errors="ignore")[:500]
                    return StreamMetric("anthropic-proxy", "http_error", status, total_s=_now() - t0, notes=body)
                current_event = ""
                for line in resp.iter_lines():
                    if not line:
                        current_event = ""
                        continue
                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip()
                        continue
                    if line.startswith("data:") and current_event == "content_block_delta":
                        raw = line.split(":", 1)[1].strip()
                        try:
                            data = json.loads(raw)
                        except Exception:
                            continue
                        text = (data.get("delta") or {}).get("text")
                        if text:
                            delta_count += 1
                            if first_delta is None:
                                first_delta = _now() - t0
                            chunks.append(str(text))
        total = _now() - t0
        status_text = "ok" if delta_count else "no_text_delta"
        notes = "Proxy emitted Anthropic content_block_delta." if delta_count else "No content_block_delta text detected."
        return StreamMetric(
            "anthropic-proxy",
            status_text,
            200,
            first_delta,
            total,
            delta_count,
            "".join(chunks)[:120],
            notes,
        )
    except Exception as exc:
        return StreamMetric("anthropic-proxy", "exception", total_s=_now() - t0, notes=repr(exc))


def render(metric: StreamMetric) -> str:
    first = "-" if metric.first_delta_s is None else f"{metric.first_delta_s:.2f}s"
    return (
        f"{metric.name}: status={metric.status}, http={metric.http_status}, "
        f"first_delta={first}, total={metric.total_s:.2f}s, "
        f"deltas={metric.delta_count}, preview={metric.text_preview!r}\n"
        f"  notes: {metric.notes}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend-base-url", default="http://127.0.0.1:8080/v1")
    parser.add_argument("--proxy-base-url", default="http://127.0.0.1:4000")
    parser.add_argument("--backend-model", default="mtplx-qwen36-27b-optimized-quality")
    parser.add_argument("--proxy-model", default="claude-opus-4-8-1m")
    parser.add_argument("--prompt", default="只回复 pong")
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()

    print("# Local Streaming Diagnostics")
    print(render(test_openai_backend(args.backend_base_url, args.backend_model, args.prompt, args.timeout)))
    print(render(test_anthropic_proxy(args.proxy_base_url, args.proxy_model, args.prompt, args.timeout)))


if __name__ == "__main__":
    main()
